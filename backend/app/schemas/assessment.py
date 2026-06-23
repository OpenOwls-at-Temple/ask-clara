from datetime import datetime
from pydantic import BaseModel


class Gap(BaseModel):
    area: str
    target_rank: int
    why: str


class Recommendation(BaseModel):
    action: str
    rationale: str


class AssessmentOut(BaseModel):
    id: str
    user_id: str
    strengths: list[str]
    gaps: list[Gap]
    recommendations: list[Recommendation]
    model: str
    created_at: datetime
