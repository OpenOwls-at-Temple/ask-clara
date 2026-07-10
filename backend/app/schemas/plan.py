from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class PlanItemOut(BaseModel):
    skill: str
    why: str
    target_rank: int | None = None
    status: Literal["pending", "complete"] = "pending"


class PlanOut(BaseModel):
    id: str
    horizon_months: int
    created_at: datetime
    items: list[PlanItemOut]


class PlanItemStatusUpdate(BaseModel):
    status: Literal["pending", "complete"]
