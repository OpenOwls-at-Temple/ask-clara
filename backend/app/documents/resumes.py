from datetime import datetime
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


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc
