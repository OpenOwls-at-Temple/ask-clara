"""Feature 8: per-posting application materials.

POST /materials/fetch-posting — resolve a pasted job-posting link into
    title/employer/description the student can review (no LLM, no quota).
POST /materials — generate the tailored resume + cover letter + employer
    brief for a posting the student provided (quota-gated).
GET /materials — list the student's saved materials (cached — viewing never
    re-calls the model).

The lead-scoped variant lives in routes/leads.py (POST /leads/:id/materials)
and shares the quota helpers below.
"""

import io
import logging
import uuid

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.documents.materials import get_materials_for_user
from app.models.user import User
from app.schemas.materials import (
    MaterialsGenerateRequest,
    MaterialsOut,
    PostingFetchRequest,
    PostingOut,
)
from app.services import materials_service
from app.services.posting_fetch import PostingFetchError, fetch_posting
from app.services.resume_pdf import render_resume_pdf, render_resume_png

logger = logging.getLogger(__name__)

LLM_GENERATION_CAP = 20

router = APIRouter()


async def consume_quota_slot(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Atomic lifetime-quota gate shared by the materials endpoints.

    Increments only while under the cap so concurrent requests cannot both
    pass; raises 429 when the student has used up their pilot allowance.
    """
    cap = 999999 if settings.environment == "local" else LLM_GENERATION_CAP
    quota_stmt = text(
        "UPDATE users SET llm_generation_count = llm_generation_count + 1 "
        "WHERE id = CAST(:user_id AS uuid) AND llm_generation_count < :cap "
        "RETURNING id"
    )
    quota_result = await db.execute(quota_stmt, {"user_id": str(user_id), "cap": cap})
    await db.commit()

    if quota_result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You have reached the generation limit for this pilot. "
                "Please contact the team if you need more."
            ),
        )


async def refund_quota_slot(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Give the quota slot back when a generation fails."""
    await db.execute(
        text(
            "UPDATE users SET llm_generation_count = llm_generation_count - 1 "
            "WHERE id = CAST(:user_id AS uuid)"
        ),
        {"user_id": str(user_id)},
    )
    await db.commit()


@router.post("/materials/fetch-posting", response_model=PostingOut)
async def fetch_posting_details(
    body: PostingFetchRequest,
    user: User = Depends(get_current_user),
):
    try:
        posting = await fetch_posting(body.url)
    except PostingFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return PostingOut(**posting)


@router.post("/materials", response_model=MaterialsOut)
async def generate_materials(
    body: MaterialsGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await consume_quota_slot(db, user.id)

    mongo = get_mongo_db()
    try:
        doc = await materials_service.generate_materials(
            db, mongo, user.id, body.model_dump()
        )
    except Exception as exc:
        await refund_quota_slot(db, user.id)
        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return MaterialsOut(**doc)


@router.get("/materials", response_model=list[MaterialsOut])
async def list_materials(
    user: User = Depends(get_current_user),
):
    mongo = get_mongo_db()
    docs = await get_materials_for_user(mongo, str(user.id))
    return [MaterialsOut(**doc) for doc in docs]


@router.get("/materials/{materials_id}/resume/download")
async def download_materials_resume(
    materials_id: str,
    format: str = "pdf",
    user: User = Depends(get_current_user),
):
    """Download the posting-tailored resume variant as a one-page Typst PDF.
    `format=png` returns an inline image used by the UI as a preview."""
    if format not in ("pdf", "png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="format must be 'pdf' or 'png'.",
        )

    mongo = get_mongo_db()
    try:
        doc = await mongo["posting_materials"].find_one({"_id": ObjectId(materials_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Materials not found."
        )

    if not doc or doc.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Materials not found."
        )

    posting = doc.get("posting", {})
    title = posting.get("title") or "resume"
    renderer = render_resume_pdf if format == "pdf" else render_resume_png
    try:
        rendered = await run_in_threadpool(
            renderer,
            user.display_name or "Resume",
            doc.get("resume_sections", []),
            None,
        )
    except Exception:
        logger.exception("Typst materials-resume rendering failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF generation failed — copy the resume text instead.",
        )

    if format == "png":
        return StreamingResponse(
            io.BytesIO(rendered),
            media_type="image/png",
            headers={"Content-Disposition": "inline"},
        )

    slug = title.lower().replace(" ", "-")
    return StreamingResponse(
        io.BytesIO(rendered),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="clara-resume-{slug}.pdf"'
        },
    )
