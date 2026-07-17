from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TargetRoleIn(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    title: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None


class ProfileIn(BaseModel):
    """Full profile save — every field except is_first_gen is required.

    An incomplete profile blocks every downstream service, so partial
    saves are rejected outright rather than persisted in a blocked state.
    """

    degree_level: str
    major_program: str = Field(..., min_length=1)
    expected_graduation: date
    track: str
    is_first_gen: Optional[bool] = None
    target_roles: list[TargetRoleIn]

    @field_validator("expected_graduation", mode="before")
    @classmethod
    def parse_expected_graduation(cls, v):
        if v == "":
            return None
        if isinstance(v, str) and len(v) == 7:
            return f"{v}-01"
        return v

    @field_validator("major_program")
    @classmethod
    def major_program_not_blank(cls, v):
        if not v.strip():
            raise ValueError("major_program is required")
        return v.strip()

    @field_validator("degree_level")
    @classmethod
    def valid_degree_level(cls, v):
        if v not in ("undergrad", "grad", "phd"):
            raise ValueError("degree_level must be undergrad, grad, or phd")
        return v

    @field_validator("track")
    @classmethod
    def valid_track(cls, v):
        if v not in (
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
        if len(roles) != 3:
            raise ValueError("All three ranked target roles are required")
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
    is_first_gen: Optional[bool] = None
    resume_doc_id: Optional[str]
    resume_filename: Optional[str] = None
    linkedin_doc_id: Optional[str]
    target_roles: list[TargetRoleOut]
