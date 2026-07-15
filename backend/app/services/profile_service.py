import logging
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.documents.linkedin import insert_linkedin
from app.documents.resumes import insert_resume
from app.models.profile import DegreeLevel, Profile, TargetRole, Track
from app.schemas.profile import ProfileIn

logger = logging.getLogger(__name__)


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


async def upsert_resume_with_consistency(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    *,
    raw_text: str,
    kind: str = "uploaded",
    structured_json: dict | None = None,
) -> str:
    """Store a resume document and link it to the user's profile.

    Cross-DB write order is a hard rule: MongoDB first, then Postgres.
    If the Postgres write fails, the new Mongo document is deleted so no
    orphan remains; on success the previously linked document is removed
    best-effort.
    """
    profile = await get_profile(db, user_id)
    old_doc_id = profile.resume_doc_id if profile else None

    doc_id = await insert_resume(
        mongo,
        {
            "user_id": str(user_id),
            "kind": kind,
            "raw_text": raw_text,
            "structured_json": structured_json or {},
        },
    )
    try:
        await set_resume_doc_id(db, user_id, doc_id)
    except Exception:
        await mongo["resumes"].delete_one({"_id": ObjectId(doc_id)})
        raise

    await _delete_stale_doc(mongo, "resumes", old_doc_id)
    return doc_id


async def upsert_linkedin_with_consistency(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    *,
    raw_text: str,
    structured_json: dict | None = None,
) -> str:
    """Store a LinkedIn document and link it to the user's profile.

    Same consistency contract as `upsert_resume_with_consistency`.
    """
    profile = await get_profile(db, user_id)
    old_doc_id = profile.linkedin_doc_id if profile else None

    doc_id = await insert_linkedin(
        mongo,
        {
            "user_id": str(user_id),
            "raw_text": raw_text,
            "structured_json": structured_json or {},
        },
    )
    try:
        await set_linkedin_doc_id(db, user_id, doc_id)
    except Exception:
        await mongo["linkedin"].delete_one({"_id": ObjectId(doc_id)})
        raise

    await _delete_stale_doc(mongo, "linkedin", old_doc_id)
    return doc_id


async def _delete_stale_doc(
    mongo: AsyncIOMotorDatabase, collection: str, doc_id: str | None
) -> None:
    if not doc_id:
        return
    try:
        await mongo[collection].delete_one({"_id": ObjectId(doc_id)})
    except Exception:
        logger.warning(
            "Failed to delete old %s document %s from MongoDB", collection, doc_id
        )
