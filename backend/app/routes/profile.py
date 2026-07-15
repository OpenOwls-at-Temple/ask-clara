from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut, TargetRoleOut
from app.services import profile_service
from app.services.document_parser_service import (
    UnsupportedFileTypeError,
    parse_document,
)

router = APIRouter()

_ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


def _profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        id=str(profile.id),
        user_id=str(profile.user_id),
        degree_level=profile.degree_level.value if profile.degree_level else None,
        major_program=profile.major_program,
        expected_graduation=profile.expected_graduation,
        track=profile.track.value,
        resume_doc_id=profile.resume_doc_id,
        linkedin_doc_id=profile.linkedin_doc_id,
        target_roles=[
            TargetRoleOut(id=str(r.id), rank=r.rank, title=r.title, notes=r.notes)
            for r in sorted(profile.target_roles, key=lambda r: r.rank)
        ],
    )


async def _read_and_parse_upload(file: UploadFile) -> str:
    """Validate an uploaded file and extract its text off the event loop."""
    content = await file.read()
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit")
    if file.content_type not in _ALLOWED_MIME and not (file.filename or "").endswith(
        (".pdf", ".docx")
    ):
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX files are accepted"
        )
    try:
        return await run_in_threadpool(
            parse_document, content, file.content_type or "", file.filename or ""
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.get_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_out(profile)


@router.put("/profile", response_model=ProfileOut)
async def upsert_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await profile_service.upsert_profile(db, user.id, body)
    return _profile_out(profile)


@router.post("/profile/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_text = await _read_and_parse_upload(file)
    doc_id = await profile_service.upsert_resume_with_consistency(
        db, get_mongo_db(), user.id, raw_text=raw_text
    )
    return {"resume_doc_id": doc_id, "preview": raw_text[:300]}


class LinkedInRequest(BaseModel):
    url: str


@router.post("/profile/linkedin")
async def submit_linkedin(
    body: LinkedInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Store the URL as a reference only; raw_text stays empty so the LLM
    # does not receive a bare URL string as "linkedin_summary".
    doc_id = await profile_service.upsert_linkedin_with_consistency(
        db,
        get_mongo_db(),
        user.id,
        raw_text="",
        structured_json={"url": body.url},
    )
    return {"linkedin_doc_id": doc_id}


@router.post("/profile/linkedin/upload")
async def upload_linkedin_export(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_text = await _read_and_parse_upload(file)
    doc_id = await profile_service.upsert_linkedin_with_consistency(
        db, get_mongo_db(), user.id, raw_text=raw_text
    )
    return {"linkedin_doc_id": doc_id, "preview": raw_text[:300]}
