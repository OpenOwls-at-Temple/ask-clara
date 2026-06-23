import uuid
from sqlalchemy.ext.asyncio import AsyncSession


async def get_profile(db: AsyncSession, user_id: uuid.UUID):
    """Return the profile + target_roles for a user, or None if not yet created."""
    raise NotImplementedError


async def upsert_profile(db: AsyncSession, user_id: uuid.UUID, data: dict):
    """Create or update the profile and its target_roles (replace all three on update)."""
    raise NotImplementedError
