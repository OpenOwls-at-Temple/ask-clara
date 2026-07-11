"""Machine-to-machine endpoints for the scheduled job scan.

These are the only routes that do not use a user session: the GitHub Actions
workflow authenticates with the SCAN_TRIGGER_SECRET shared secret (set in both
Render and GitHub Actions secrets — see ai_specs/architecture-planning.md).
"""

import hmac

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from app.config import settings
from app.database import AsyncSessionLocal
from app.services import lead_service

router = APIRouter()

_SECRET_HEADER = "X-Scan-Trigger-Secret"


def _require_scan_secret(provided: str | None) -> None:
    if not settings.scan_trigger_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job scanning is not configured on this environment.",
        )
    if not provided or not hmac.compare_digest(provided, settings.scan_trigger_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scan secret."
        )


async def _run_scan_task() -> None:
    # Background task outlives the request, so it opens its own DB session.
    async with AsyncSessionLocal() as db:
        await lead_service.run_scan(db)


@router.post("/admin/scan-jobs", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    background_tasks: BackgroundTasks,
    secret: str | None = Header(default=None, alias=_SECRET_HEADER),
):
    _require_scan_secret(secret)
    if lead_service.get_scan_status().get("state") == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A scan is already running."
        )
    background_tasks.add_task(_run_scan_task)
    return {"status": "started"}


@router.get("/admin/scan-jobs/status")
async def scan_status(
    secret: str | None = Header(default=None, alias=_SECRET_HEADER),
):
    _require_scan_secret(secret)
    return lead_service.get_scan_status()
