import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, get_mongo_db
from app.models.lead import JobLead
from app.models.user import User
from app.routes.materials import consume_quota_slot, refund_quota_slot
from app.schemas.lead import LeadOut, LeadStatusUpdate
from app.schemas.materials import LeadMaterialsRequest, MaterialsOut
from app.services import lead_service, materials_service, profile_service
from app.services.posting_fetch import PostingFetchError

logger = logging.getLogger(__name__)

SCAN_COOLDOWN_HOURS = 24

router = APIRouter()


async def consume_scan_slot(db: AsyncSession, user_id: uuid.UUID) -> datetime | None:
    """Atomic once-per-24h gate for the manual leads scan.

    Stamps last_lead_scan_at only if the cooldown has elapsed, so concurrent
    requests cannot both pass. Returns the previous timestamp so a failed
    scan can restore it; raises 429 while the cooldown is active.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(hours=SCAN_COOLDOWN_HOURS)

    prev_result = await db.execute(
        text("SELECT last_lead_scan_at FROM users WHERE id = CAST(:user_id AS uuid)"),
        {"user_id": str(user_id)},
    )
    prev = prev_result.scalar_one()

    result = await db.execute(
        text(
            "UPDATE users SET last_lead_scan_at = :now "
            "WHERE id = CAST(:user_id AS uuid) "
            "AND (last_lead_scan_at IS NULL OR last_lead_scan_at <= :cutoff) "
            "RETURNING id"
        ),
        {"user_id": str(user_id), "now": now, "cutoff": cutoff},
    )
    await db.commit()

    if result.rowcount == 0:
        next_allowed = prev + timedelta(hours=SCAN_COOLDOWN_HOURS) if prev else now
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You can run a manual scan once per day. "
                f"Try again after {next_allowed.isoformat()}Z."
            ),
        )
    return prev


async def refund_scan_slot(
    db: AsyncSession, user_id: uuid.UUID, prev: datetime | None
) -> None:
    """Restore the pre-scan timestamp when a manual scan fails."""
    await db.execute(
        text(
            "UPDATE users SET last_lead_scan_at = :prev "
            "WHERE id = CAST(:user_id AS uuid)"
        ),
        {"user_id": str(user_id), "prev": prev},
    )
    await db.commit()


@router.post("/leads/scan")
async def scan_leads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Feature 7: student-triggered scan of their own profile, once per 24h.

    The profile check runs before the slot is consumed so an incomplete
    profile never burns the daily allowance.
    """
    profile = await profile_service.get_profile(db, user.id)
    if profile is None or not profile.target_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add your ranked target roles before scanning for leads.",
        )

    prev = await consume_scan_slot(db, user.id)
    try:
        created = await lead_service.scan_for_user(db, profile)
    except Exception:
        logger.exception("Manual lead scan failed for user %s", user.id)
        await refund_scan_slot(db, user.id, prev)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The scan failed — please try again later.",
        )
    return {"created": created}


def _to_lead_out(lead: JobLead) -> LeadOut:
    return LeadOut(
        id=str(lead.id),
        source=lead.source,
        url=lead.url,
        title=lead.title,
        employer=lead.employer,
        fit_score=lead.fit_score,
        fit_reason=lead.fit_reason,
        status=lead.status.value,
        found_at=lead.found_at,
    )


@router.get("/leads", response_model=list[LeadOut])
async def list_leads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    leads = await lead_service.list_leads(db, user.id)
    return [_to_lead_out(lead) for lead in leads]


@router.post("/leads/mark-seen")
async def mark_leads_seen(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await lead_service.mark_new_leads_seen(db, user.id)
    return {"updated": updated}


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: str,
    body: LeadStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        lead_uuid = uuid.UUID(lead_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found."
        )

    lead = await lead_service.update_lead_status(db, user.id, lead_uuid, body.status)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found."
        )
    return _to_lead_out(lead)


@router.post("/leads/{lead_id}/materials", response_model=MaterialsOut)
async def generate_lead_materials(
    lead_id: str,
    body: LeadMaterialsRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Feature 8: tailored resume + cover letter + employer brief for one lead.

    If the request body carries no pasted description, Clara fetches the
    lead's original posting page; when that fails, a 422 asks the student to
    paste the description manually.
    """
    try:
        lead_uuid = uuid.UUID(lead_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found."
        )

    # Ownership is verified before the quota slot is consumed.
    lead = await materials_service.get_owned_lead(db, user.id, lead_uuid)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found."
        )

    await consume_quota_slot(db, user.id)

    mongo = get_mongo_db()
    try:
        doc = await materials_service.generate_for_lead(
            db, mongo, user.id, lead, description=body.description if body else None
        )
    except Exception as exc:
        await refund_quota_slot(db, user.id)
        if isinstance(exc, PostingFetchError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            )
        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )

    return MaterialsOut(**doc)
