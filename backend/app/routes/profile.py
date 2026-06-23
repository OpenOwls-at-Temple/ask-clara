from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter()


@router.get("/profile", response_model=ProfileOut)
async def get_profile(db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; call profile_service.get_profile(user_id)
    raise NotImplementedError


@router.put("/profile", response_model=ProfileOut)
async def upsert_profile(body: ProfileIn, db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; call profile_service.upsert_profile(user_id, body)
    raise NotImplementedError


@router.post("/profile/resume")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # TODO: validate PDF/DOCX, parse text, write to MongoDB first then update
    #       profiles.resume_doc_id in Postgres; return confirmation
    raise NotImplementedError


@router.post("/profile/linkedin")
async def submit_linkedin(db: AsyncSession = Depends(get_db)):
    # TODO: accept URL or exported PDF; extract content; store in MongoDB;
    #       update profiles.linkedin_doc_id
    raise NotImplementedError
