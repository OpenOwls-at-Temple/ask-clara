from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


@router.post("/resumes/generate")
async def generate_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: check quota; call assessment_service.generate_resumes(db, mongo, user.id);
    #       persist three resume documents to MongoDB
    raise NotImplementedError


@router.get("/resumes")
async def list_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: return user's resume drafts from MongoDB for user.id
    raise NotImplementedError
