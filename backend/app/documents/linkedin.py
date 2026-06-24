from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


async def insert_linkedin(mongo: AsyncIOMotorDatabase, doc: dict) -> str:
    """Insert a LinkedIn document and return its string _id.

    doc shape: { user_id, raw_text, structured_json, created_at }
    """
    doc.setdefault("created_at", datetime.utcnow())
    result = await mongo["linkedin"].insert_one(doc)
    return str(result.inserted_id)


async def get_linkedin_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> dict | None:
    doc = await mongo["linkedin"].find_one(
        {"user_id": user_id}, sort=[("created_at", -1)]
    )
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc
