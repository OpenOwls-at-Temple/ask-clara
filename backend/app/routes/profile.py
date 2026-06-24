import io

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.documents.linkedin import insert_linkedin
from app.documents.resumes import insert_resume
from app.models.profile import Profile, TargetRole
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut, TargetRoleOut
from app.services import profile_service

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


def _parse_resume(content: bytes, content_type: str, filename: str) -> str:
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    if content_type == "application/pdf" or ext == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx" or "wordprocessingml" in content_type:
        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    raise HTTPException(
        status_code=400, detail="Unsupported file type. Upload a PDF or DOCX."
    )


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
    content = await file.read()
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit")
    if file.content_type not in _ALLOWED_MIME and not (file.filename or "").endswith(
        (".pdf", ".docx")
    ):
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX files are accepted"
        )

    raw_text = _parse_resume(content, file.content_type or "", file.filename or "")

    mongo = get_mongo_db()
    doc_id = await insert_resume(
        mongo,
        {
            "user_id": str(user.id),
            "kind": "uploaded",
            "raw_text": raw_text,
            "structured_json": {},
        },
    )

    # Write MongoDB document first; compensate if Postgres update fails.
    try:
        await profile_service.set_resume_doc_id(db, user.id, doc_id)
    except Exception:
        await mongo["resumes"].delete_one({"_id": ObjectId(doc_id)})
        raise

    return {"resume_doc_id": doc_id, "preview": raw_text[:300]}


class LinkedInRequest(BaseModel):
    url: str


@router.post("/profile/linkedin")
async def submit_linkedin(
    body: LinkedInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mongo = get_mongo_db()
    doc_id = await insert_linkedin(
        mongo,
        {
            "user_id": str(user.id),
            "raw_text": body.url,
            "structured_json": {"url": body.url},
        },
    )

    try:
        await profile_service.set_linkedin_doc_id(db, user.id, doc_id)
    except Exception:
        await mongo["linkedin"].delete_one({"_id": ObjectId(doc_id)})
        raise

    return {"linkedin_doc_id": doc_id}
