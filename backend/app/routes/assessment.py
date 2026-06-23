from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.assessment import AssessmentOut

router = APIRouter()


@router.post("/assessment", response_model=AssessmentOut)
async def run_assessment(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: check llm_generation_count quota atomically (UPDATE ... WHERE count < cap RETURNING);
    #       call assessment_service.run_assessment(db, mongo, user.id);
    #       persist result to MongoDB assessments collection
    raise NotImplementedError


@router.get("/assessment", response_model=list[AssessmentOut])
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: return saved assessments from MongoDB for user.id (never re-run the model)
    raise NotImplementedError
