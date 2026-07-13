from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LeadOut(BaseModel):
    id: str
    source: str
    url: str
    title: str
    employer: str
    fit_score: float | None = None
    fit_reason: str | None = None
    status: Literal["new", "seen", "applied", "dismissed"]
    found_at: datetime


class LeadStatusUpdate(BaseModel):
    # "new" is system-assigned at scan time; students move leads forward only.
    status: Literal["seen", "applied", "dismissed"]
