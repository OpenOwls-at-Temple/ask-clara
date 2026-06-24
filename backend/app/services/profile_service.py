import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import DegreeLevel, Profile, TargetRole, Track
from app.schemas.profile import ProfileIn


async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    stmt = (
        select(Profile)
        .where(Profile.user_id == user_id)
        .options(selectinload(Profile.target_roles))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_profile(
    db: AsyncSession, user_id: uuid.UUID, data: ProfileIn
) -> Profile:
    profile = await get_profile(db, user_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if profile is None:
        profile = Profile(id=uuid.uuid4(), user_id=user_id, updated_at=now)
        db.add(profile)
    else:
        profile.updated_at = now

    if data.degree_level is not None:
        profile.degree_level = DegreeLevel(data.degree_level)
    if data.major_program is not None:
        profile.major_program = data.major_program
    if data.expected_graduation is not None:
        profile.expected_graduation = data.expected_graduation
    if data.track is not None:
        profile.track = Track(data.track)
    if data.is_first_gen is not None:
        profile.is_first_gen = data.is_first_gen

    # Flush to get profile.id before inserting target_roles.
    await db.flush()

    if data.target_roles is not None:
        await db.execute(delete(TargetRole).where(TargetRole.profile_id == profile.id))
        for role in data.target_roles:
            db.add(
                TargetRole(
                    id=uuid.uuid4(),
                    profile_id=profile.id,
                    rank=role.rank,
                    title=role.title,
                    notes=role.notes,
                )
            )

    await db.commit()
    db.expire(profile)
    # Reload with relationships populated.
    return await get_profile(db, user_id)


async def set_resume_doc_id(db: AsyncSession, user_id: uuid.UUID, doc_id: str) -> None:
    profile = await get_profile(db, user_id)
    if profile is None:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=user_id,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(profile)
    profile.resume_doc_id = doc_id
    profile.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()


async def set_linkedin_doc_id(
    db: AsyncSession, user_id: uuid.UUID, doc_id: str
) -> None:
    profile = await get_profile(db, user_id)
    if profile is None:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=user_id,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(profile)
    profile.linkedin_doc_id = doc_id
    profile.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
