import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def upsert_user(db: AsyncSession, *, email: str, display_name: str) -> User:
    """Create or update a User row on every successful Google sign-in."""
    stmt = select(User).where(User.temple_email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user is None:
        user = User(
            id=uuid.uuid4(),
            temple_email=email,
            display_name=display_name,
            role=UserRole.student,
            llm_generation_count=0,
            created_at=now,
            last_login_at=now,
        )
        db.add(user)
    else:
        user.last_login_at = now
        if display_name and display_name != user.display_name:
            user.display_name = display_name

    await db.commit()
    await db.refresh(user)
    return user
