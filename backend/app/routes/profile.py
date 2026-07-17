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
# LinkedIn's "Get a copy of your data" export produces CSV files (Profile.csv,
# Positions.csv, ...), so the LinkedIn upload additionally accepts CSV.
_LINKEDIN_ALLOWED_MIME = _ALLOWED_MIME | {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",  # some browsers label .csv this way
}
_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


def _sanitize_filename(filename: str | None) -> str | None:
    """Reduce a client-supplied filename to a safe display string."""
    if not filename:
        return None
    # Browsers may send a full path; keep only the last segment.
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(c for c in name if c.isprintable()).strip()
    return name[:255] or None


def _profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        id=str(profile.id),
        user_id=str(profile.user_id),
        degree_level=profile.degree_level.value if profile.degree_level else None,
        major_program=profile.major_program,
        expected_graduation=profile.expected_graduation,
        track=profile.track.value,
        is_first_gen=profile.is_first_gen,
        resume_doc_id=profile.resume_doc_id,
        resume_filename=profile.resume_filename,
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


def _parse_csv_export(content: bytes) -> str:
    """Flatten a LinkedIn data-export CSV into readable "Header: value" lines.

    Export CSVs (Profile.csv, Positions.csv, Education.csv, ...) have one
    header row; each data row becomes a block of non-empty fields so the text
    reads like profile content rather than a raw table.
    """
    import csv
    import io

    text = content.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return ""
    header, *data = rows
    blocks = []
    for row in data:
        lines = [
            f"{header[i].strip()}: {value.strip()}"
            for i, value in enumerate(row)
            if i < len(header) and value.strip()
        ]
        if lines:
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _parse_linkedin_export(content: bytes, content_type: str, filename: str) -> str:
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    if ext == "csv" or "csv" in content_type:
        return _parse_csv_export(content)
    return _parse_resume(content, content_type, filename)


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
    resume_filename = _sanitize_filename(file.filename)
    doc_id = await profile_service.upsert_resume_with_consistency(
        db, get_mongo_db(), user.id, raw_text=raw_text, filename=resume_filename
    )
    return {
        "resume_doc_id": doc_id,
        "resume_filename": resume_filename,
        "preview": raw_text[:300],
    }


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
    content = await file.read()
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit")
    if file.content_type not in _LINKEDIN_ALLOWED_MIME and not (
        file.filename or ""
    ).endswith((".pdf", ".docx", ".csv")):
        raise HTTPException(
            status_code=400, detail="Only PDF, DOCX, and CSV files are accepted"
        )

    raw_text = await run_in_threadpool(
        _parse_linkedin_export, content, file.content_type or "", file.filename or ""
    )
    doc_id = await profile_service.upsert_linkedin_with_consistency(
        db, get_mongo_db(), user.id, raw_text=raw_text
    )
    return {"linkedin_doc_id": doc_id, "preview": raw_text[:300]}
