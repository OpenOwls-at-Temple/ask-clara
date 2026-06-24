import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class DegreeLevel(str, enum.Enum):
    undergrad = "undergrad"
    grad = "grad"
    phd = "phd"


class Track(str, enum.Enum):
    industry = "industry"
    academia = "academia"
    government = "government"
    undecided = "undecided"


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    degree_level: Mapped[DegreeLevel | None] = mapped_column(
        SAEnum(DegreeLevel), nullable=True
    )
    major_program: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_graduation: Mapped[date | None] = mapped_column(Date, nullable=True)
    track: Mapped[Track] = mapped_column(SAEnum(Track), default=Track.undecided)
    is_first_gen: Mapped[bool | None] = mapped_column(nullable=True)
    resume_doc_id: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_doc_id: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    target_roles: Mapped[list["TargetRole"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class TargetRole(Base):
    __tablename__ = "target_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, or 3
    title: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile: Mapped["Profile"] = relationship(back_populates="target_roles")
