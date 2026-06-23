from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.post("/resumes/generate")
async def generate_resumes(db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; check quota; call assessment_service.generate_resumes(user_id);
    #       persist three resume documents to MongoDB; return list
    raise NotImplementedError


@router.get("/resumes")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; return user's resume drafts from MongoDB
    raise NotImplementedError
