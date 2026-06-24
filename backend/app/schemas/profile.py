from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TargetRoleIn(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    title: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None


class ProfileIn(BaseModel):
    degree_level: Optional[str] = None
    major_program: Optional[str] = None
    expected_graduation: Optional[date] = None
    track: Optional[str] = None
    is_first_gen: Optional[bool] = None
    target_roles: Optional[list[TargetRoleIn]] = None

    @field_validator("expected_graduation", mode="before")
    @classmethod
    def parse_expected_graduation(cls, v):
        if v == "" or v is None:
            return None
        if isinstance(v, str) and len(v) == 7:
            return f"{v}-01"
        return v

    @field_validator("degree_level")
    @classmethod
    def valid_degree_level(cls, v):
        if v is not None and v not in ("undergrad", "grad", "phd"):
            raise ValueError("degree_level must be undergrad, grad, or phd")
        return v

    @field_validator("track")
    @classmethod
    def valid_track(cls, v):
        if v is not None and v not in (
            "industry",
            "academia",
            "government",
            "undecided",
        ):
            raise ValueError(
                "track must be industry, academia, government, or undecided"
            )
        return v

    @model_validator(mode="after")
    def validate_target_roles(self):
        roles = self.target_roles
        if roles is None:
            return self
        if len(roles) > 3:
            raise ValueError("A maximum of three target roles may be submitted")
        ranks = [r.rank for r in roles]
        if len(ranks) != len(set(ranks)):
            raise ValueError("Target role ranks must be unique")
        return self


class TargetRoleOut(BaseModel):
    id: str
    rank: int
    title: str
    notes: Optional[str]


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
