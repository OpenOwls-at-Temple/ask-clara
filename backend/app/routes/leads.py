import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.lead import JobLead
from app.models.user import User
from app.schemas.lead import LeadOut, LeadStatusUpdate
from app.services import lead_service

router = APIRouter()


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


@router.post("/leads/{lead_id}/materials")
async def generate_lead_materials(
    lead_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Feature 8 (per-posting resume + cover letter + employer brief) — not yet implemented.
    raise NotImplementedError
