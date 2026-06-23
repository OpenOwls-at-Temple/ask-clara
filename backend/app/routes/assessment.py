from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.assessment import AssessmentOut

router = APIRouter()


@router.post("/assessment", response_model=AssessmentOut)
async def run_assessment(db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; check llm_generation_count quota atomically;
    #       call assessment_service.run(user_id); persist to MongoDB + Postgres ref
    raise NotImplementedError


@router.get("/assessment", response_model=list[AssessmentOut])
async def list_assessments(db: AsyncSession = Depends(get_db)):
    # TODO: get_current_user dep; return saved assessments from MongoDB
    raise NotImplementedError
