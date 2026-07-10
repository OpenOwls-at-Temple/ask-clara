import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class DevelopmentPlan(Base):
    __tablename__ = "development_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id"), nullable=False, index=True
    )
    horizon_months: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # List of {skill, why, target_rank, status}; status is injected by the backend
    # (pending -> complete) — the LLM never produces or sees it.
    items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
