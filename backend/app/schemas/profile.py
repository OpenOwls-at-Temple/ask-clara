from datetime import date
from pydantic import BaseModel, Field
from typing import Optional


class TargetRoleIn(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    title: str
    notes: Optional[str] = None


class ProfileIn(BaseModel):
    degree_level: Optional[str] = None
    major_program: Optional[str] = None
    expected_graduation: Optional[date] = None
    track: Optional[str] = None
    is_first_gen: Optional[bool] = None
    target_roles: list[TargetRoleIn] = Field(default_factory=list, max_length=3)


class TargetRoleOut(TargetRoleIn):
    id: str


class ProfileOut(BaseModel):
    id: str
    user_id: str
    degree_level: Optional[str]
    major_program: Optional[str]
    expected_graduation: Optional[date]
    track: str
    resume_doc_id: Optional[str]
    linkedin_doc_id: Optional[str]
    target_roles: list[TargetRoleOut]
