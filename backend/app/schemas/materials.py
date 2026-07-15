from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.resume import ResumeSectionOut


class PostingFetchRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2000)


class PostingOut(BaseModel):
    title: str
    employer: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: str


class MaterialsGenerateRequest(BaseModel):
    """A posting the student provided — fetched-and-confirmed or entered manually."""

    title: str = Field(min_length=1, max_length=200)
    employer: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=20_000)
    location: Optional[str] = Field(default=None, max_length=200)
    url: Optional[str] = Field(default=None, max_length=2000)


class LeadMaterialsRequest(BaseModel):
    # Pasted by the student when Clara can't fetch the lead's posting page.
    description: Optional[str] = Field(default=None, max_length=20_000)


class MaterialsOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    posting: PostingOut
    fit_summary: str
    resume_sections: list[ResumeSectionOut]
    cover_letter: str
    employer_brief: str
    notes_for_student: list[str]
    model: Optional[str] = None
    created_at: datetime
