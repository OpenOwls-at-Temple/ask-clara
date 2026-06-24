from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ResumeSectionOut(BaseModel):
    heading: str
    content: str


class ResumeOut(BaseModel):
    id: str
    user_id: str
    kind: str
    target_rank: Optional[int] = None
    target_title: Optional[str] = None
    sections: list[ResumeSectionOut]
    notes_for_student: list[str]
    raw_text: str
    edited_text: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime


class ResumeEditRequest(BaseModel):
    edited_text: str
