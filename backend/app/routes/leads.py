from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()

# Phase 2 endpoints — not implemented in Phase 1


@router.get("/leads")
async def list_leads(db: AsyncSession = Depends(get_db)):
    raise NotImplementedError


@router.post("/leads/{lead_id}/materials")
async def generate_lead_materials(lead_id: str, db: AsyncSession = Depends(get_db)):
    raise NotImplementedError
