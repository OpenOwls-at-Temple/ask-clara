import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    student = "student"
    counselor = "counselor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    temple_email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.student)
    llm_generation_count: Mapped[int] = mapped_column(Integer, default=0)
    # Bumped on logout to revoke all outstanding refresh tokens (each refresh
    # JWT carries the version it was minted with; a mismatch on /refresh = 401).
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Backs the once-per-24h limit on the student-triggered job-leads scan.
    last_lead_scan_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
