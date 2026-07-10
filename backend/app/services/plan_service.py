import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.assessments import get_latest_assessment_for_user
from app.llm.agents import run_planning_agent
from app.llm.orchestrator import build_plan_context
from app.llm.service import FALLBACK_MESSAGE
from app.models.plan import DevelopmentPlan
from app.models.profile import Profile
from app.services import profile_service

DEFAULT_HORIZON_MONTHS = 6
VALID_ITEM_STATUSES = ("pending", "complete")


async def generate_plan(
    db: AsyncSession, mongo: AsyncIOMotorDatabase, user_id: uuid.UUID
) -> DevelopmentPlan:
    """Run the planning agent and persist the result.

    1. Load profile + ranked target roles from Postgres and the latest saved
       assessment from MongoDB (a plan is derived from an assessment).
    2. Call the planning agent with trimmed context.
    3. Inject status='pending' into each item — the model never produces status.
    4. Persist a new development_plans row and return it.
    """
    profile = await profile_service.get_profile(db, user_id)
    if profile is None:
        raise ValueError("Profile not found. Please complete your profile first.")
    if not profile.target_roles:
        raise ValueError("Please add your target roles before generating a plan.")

    assessment = await get_latest_assessment_for_user(mongo, str(user_id))
    if assessment is None:
        raise ValueError(
            "Please run an assessment before generating a development plan."
        )

    profile_dict = {
        "degree_level": profile.degree_level.value if profile.degree_level else None,
        "major_program": profile.major_program,
        "track": profile.track.value if profile.track else None,
        "target_roles": [
            {"rank": r.rank, "title": r.title} for r in profile.target_roles
        ],
    }
    context = build_plan_context(profile_dict, assessment)

    result = await run_planning_agent(context)
    if "error" in result:
        raise RuntimeError(result["error"])

    items = [
        {
            "skill": str(item.get("skill", "")),
            "why": str(item.get("why", "")),
            "target_rank": _coerce_rank(item.get("target_rank")),
            "status": "pending",
        }
        for item in result.get("items", [])
        if isinstance(item, dict) and item.get("skill")
    ]
    if not items:
        raise RuntimeError(FALLBACK_MESSAGE)

    plan = DevelopmentPlan(
        id=uuid.uuid4(),
        profile_id=profile.id,
        horizon_months=_coerce_horizon(result.get("horizon_months")),
        items=items,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_latest_plan(
    db: AsyncSession, user_id: uuid.UUID
) -> DevelopmentPlan | None:
    stmt = (
        select(DevelopmentPlan)
        .join(Profile, DevelopmentPlan.profile_id == Profile.id)
        .where(Profile.user_id == user_id)
        .order_by(DevelopmentPlan.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_item_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_id: uuid.UUID,
    item_index: int,
    status: str,
) -> DevelopmentPlan | None:
    """Set one plan item's status. Returns None if the plan does not belong
    to the user or the item index is out of range.
    """
    if status not in VALID_ITEM_STATUSES:
        raise ValueError(f"Invalid status '{status}'.")

    stmt = (
        select(DevelopmentPlan)
        .join(Profile, DevelopmentPlan.profile_id == Profile.id)
        .where(Profile.user_id == user_id, DevelopmentPlan.id == plan_id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if plan is None:
        return None
    if not 0 <= item_index < len(plan.items):
        return None

    # Reassign a new list so SQLAlchemy detects the JSONB change.
    items = [dict(item) for item in plan.items]
    items[item_index]["status"] = status
    plan.items = items
    await db.commit()
    await db.refresh(plan)
    return plan


def _coerce_rank(value) -> int | None:
    try:
        rank = int(value)
    except (TypeError, ValueError):
        return None
    return rank if rank in (1, 2, 3) else None


def _coerce_horizon(value) -> int:
    try:
        horizon = int(value)
    except (TypeError, ValueError):
        return DEFAULT_HORIZON_MONTHS
    return horizon if 1 <= horizon <= 24 else DEFAULT_HORIZON_MONTHS
