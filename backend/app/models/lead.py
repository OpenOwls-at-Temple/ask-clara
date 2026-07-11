import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class LeadStatus(str, enum.Enum):
    new = "new"
    seen = "seen"
    applied = "applied"
    dismissed = "dismissed"


class JobLead(Base):
    __tablename__ = "job_leads"
    # One lead per posting per student — the scan skips URLs already stored.
    __table_args__ = (
        UniqueConstraint("profile_id", "url", name="uq_job_leads_profile_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    employer: Mapped[str] = mapped_column(String, nullable=False)
    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        SAEnum(LeadStatus), nullable=False, default=LeadStatus.new
    )
    found_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
