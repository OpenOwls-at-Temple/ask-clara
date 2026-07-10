import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.models.plan import DevelopmentPlan
from app.models.user import User
from app.schemas.plan import PlanItemStatusUpdate, PlanOut
from app.services import plan_service

LLM_GENERATION_CAP = 20

router = APIRouter()


def _to_plan_out(plan: DevelopmentPlan) -> PlanOut:
    return PlanOut(
        id=str(plan.id),
        horizon_months=plan.horizon_months,
        created_at=plan.created_at,
        items=plan.items,
    )


@router.post("/plan/generate", response_model=PlanOut)
async def generate_plan(
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
    quota_result = await db.execute(quota_stmt, {"user_id": str(user.id), "cap": cap})
    await db.commit()

    if quota_result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You have reached the generation limit for this pilot. "
                "Please contact the team if you need more."
            ),
        )

    mongo = get_mongo_db()
    try:
        plan = await plan_service.generate_plan(db, mongo, user.id)
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return _to_plan_out(plan)


@router.get("/plan", response_model=PlanOut | None)
async def get_plan(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await plan_service.get_latest_plan(db, user.id)
    if plan is None:
        return None
    return _to_plan_out(plan)


@router.patch("/plan/{plan_id}/items/{item_index}", response_model=PlanOut)
async def update_plan_item(
    plan_id: str,
    item_index: int,
    body: PlanItemStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        plan_uuid = uuid.UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )

    plan = await plan_service.update_item_status(
        db, user.id, plan_uuid, item_index, body.status
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found."
        )
    return _to_plan_out(plan)
