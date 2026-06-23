from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter()


@router.get("/profile", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: call profile_service.get_profile(db, user.id)
    raise NotImplementedError


@router.put("/profile", response_model=ProfileOut)
async def upsert_profile(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: call profile_service.upsert_profile(db, user.id, body)
    raise NotImplementedError


@router.post("/profile/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: validate PDF/DOCX; parse text with pypdf/python-docx;
    #       write to MongoDB resumes (kind='uploaded') FIRST, then update
    #       profiles.resume_doc_id in Postgres
    raise NotImplementedError


@router.post("/profile/linkedin")
async def submit_linkedin(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: accept URL or exported PDF; extract content; store in MongoDB linkedin;
    #       update profiles.linkedin_doc_id
    raise NotImplementedError
