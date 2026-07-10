from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


async def insert_assessment(mongo: AsyncIOMotorDatabase, doc: dict) -> str:
    """Insert an assessment document and return its string _id.

    doc shape: { user_id, strengths[], gaps[], recommendations[], model, created_at }
    """
    doc.setdefault("created_at", datetime.utcnow())
    result = await mongo["assessments"].insert_one(doc)
    return str(result.inserted_id)


async def get_assessments_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> list[dict]:
    cursor = mongo["assessments"].find({"user_id": user_id}).sort("created_at", -1)
    return [_serialize(doc) async for doc in cursor]


async def get_latest_assessment_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> dict | None:
    doc = await mongo["assessments"].find_one(
        {"user_id": user_id}, sort=[("created_at", -1)]
    )
    return _serialize(doc) if doc else None


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc
