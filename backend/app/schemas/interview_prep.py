from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PrepPostingIn(BaseModel):
    """A specific posting to prepare for. Only the title is required — unlike
    Feature 8, prep is still useful from a job title and employer alone, so a
    missing description degrades the result rather than blocking it."""

    title: str = Field(min_length=1, max_length=200)
    employer: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=20_000)
    url: Optional[str] = Field(default=None, max_length=2000)


class InterviewPrepRequest(BaseModel):
    """Prep for one of the student's ranked target roles, or for a posting."""

    target_rank: Optional[int] = Field(default=None, ge=1, le=3)
    posting: Optional[PrepPostingIn] = None

    @model_validator(mode="after")
    def exactly_one_target(self):
        if (self.target_rank is None) == (self.posting is None):
            raise ValueError("Provide either target_rank or posting, not both.")
        return self


class PrepTargetOut(BaseModel):
    mode: str  # "role" | "posting"
    title: str
    employer: Optional[str] = None
    url: Optional[str] = None
    rank: Optional[int] = None


class InterviewFormatOut(BaseModel):
    name: str
    what_to_expect: str
    how_to_prepare: str


class FocusAreaOut(BaseModel):
    area: str
    why: str
    how_to_prepare: str


class PracticeQuestionOut(BaseModel):
    question: str
    type: str
    what_they_look_for: str


class InterviewPrepOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    target: PrepTargetOut
    formats: list[InterviewFormatOut]
    focus_areas: list[FocusAreaOut]
    practice_questions: list[PracticeQuestionOut]
    questions_to_ask: list[str]
    notes_for_student: list[str]
    model: Optional[str] = None
    created_at: datetime
