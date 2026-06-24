from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.documents.assessments import get_assessments_for_user
from app.models.user import User
from app.schemas.assessment import AssessmentOut
from app.services import assessment_service

LLM_GENERATION_CAP = 20

router = APIRouter()


@router.post("/assessment", response_model=AssessmentOut)
async def run_assessment(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Atomic quota gate: increment only if under the cap so concurrent requests cannot
    # both pass. Returns no rows if the user is already at or above the cap.
    cap = 999999 if settings.environment == "local" else LLM_GENERATION_CAP
    quota_stmt = text(
        "UPDATE users SET llm_generation_count = llm_generation_count + 1 "
        "WHERE id = CAST(:user_id AS uuid) AND llm_generation_count < :cap "
        "RETURNING id"
    )
    quota_result = await db.execute(
        quota_stmt, {"user_id": str(user.id), "cap": cap}
    )
    await db.commit()

    if quota_result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You have reached the assessment limit for this pilot. "
                "Please contact the team if you need more."
            ),
        )

    mongo = get_mongo_db()
    try:
        doc = await assessment_service.run_assessment(db, mongo, user.id)
    except Exception as exc:
        # Refund the quota slot since the generation failed
        await db.execute(
            text(
                "UPDATE users SET llm_generation_count = llm_generation_count - 1 "
                "WHERE id = CAST(:user_id AS uuid)"
            ),
            {"user_id": str(user.id)},
        )
        await db.commit()
        if isinstance(exc, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return AssessmentOut(**doc)


@router.get("/assessment", response_model=list[AssessmentOut])
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mongo = get_mongo_db()
    docs = await get_assessments_for_user(mongo, str(user.id))
    return [AssessmentOut(**doc) for doc in docs]
