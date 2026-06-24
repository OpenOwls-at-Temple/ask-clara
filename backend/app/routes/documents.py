from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.documents.resumes import get_generated_resumes_for_user, update_resume_edited_text
from app.models.user import User
from app.schemas.resume import ResumeEditRequest, ResumeOut
from app.services import assessment_service

LLM_GENERATION_CAP = 20

router = APIRouter()


@router.post("/resumes/generate", response_model=list[ResumeOut])
async def generate_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quota_stmt = text(
        "UPDATE users SET llm_generation_count = llm_generation_count + 1 "
        "WHERE id = CAST(:user_id AS uuid) AND llm_generation_count < :cap "
        "RETURNING id"
    )
    quota_result = await db.execute(
        quota_stmt, {"user_id": str(user.id), "cap": LLM_GENERATION_CAP}
    )
    await db.commit()

    if quota_result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You have reached the generation limit for this pilot. "
                "Please contact the team if you need more."
            ),
        )

    mongo = get_mongo_db()
    try:
        docs = await assessment_service.generate_resumes(db, mongo, user.id)
    except ValueError as exc:
        await db.execute(
            text(
                "UPDATE users SET llm_generation_count = llm_generation_count - 1 "
                "WHERE id = CAST(:user_id AS uuid)"
            ),
            {"user_id": str(user.id)},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return [ResumeOut(**doc) for doc in docs]


@router.get("/resumes", response_model=list[ResumeOut])
async def list_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mongo = get_mongo_db()
    docs = await get_generated_resumes_for_user(mongo, str(user.id))
    return [ResumeOut(**doc) for doc in docs]


@router.patch("/resumes/{resume_id}")
async def update_resume(
    resume_id: str,
    body: ResumeEditRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mongo = get_mongo_db()
    updated = await update_resume_edited_text(mongo, resume_id, str(user.id), body.edited_text)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return {"ok": True}
