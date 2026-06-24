from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def insert_resume(mongo: AsyncIOMotorDatabase, doc: dict) -> str:
    """Insert a resume document and return its string _id.

    doc shape: { user_id, kind: 'uploaded'|'generated', target_rank (optional),
                 raw_text, structured_json, created_at }
    """
    doc.setdefault("created_at", datetime.utcnow())
    result = await mongo["resumes"].insert_one(doc)
    return str(result.inserted_id)


async def get_resumes_for_user(mongo: AsyncIOMotorDatabase, user_id: str) -> list[dict]:
    cursor = mongo["resumes"].find({"user_id": user_id})
    return [_serialize(doc) async for doc in cursor]


async def get_generated_resumes_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> list[dict]:
    cursor = (
        mongo["resumes"]
        .find({"user_id": user_id, "kind": "generated"})
        .sort("target_rank", 1)
    )
    return [_serialize(doc) async for doc in cursor]


async def update_resume_edited_text(
    mongo: AsyncIOMotorDatabase, resume_id: str, user_id: str, edited_text: str
) -> bool:
    """Set edited_text on a resume owned by user_id. Returns True if found."""
    try:
        oid = ObjectId(resume_id)
    except InvalidId:
        return False
    result = await mongo["resumes"].update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {"edited_text": edited_text}},
    )
    return result.matched_count > 0


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc
