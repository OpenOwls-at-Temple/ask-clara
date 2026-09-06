from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


async def insert_interview_prep(mongo: AsyncIOMotorDatabase, doc: dict) -> str:
    """Insert an interview-prep document and return its string _id.

    doc shape: { user_id, lead_id (optional), target: {mode, title, employer,
                 url, rank}, formats[], focus_areas[], practice_questions[],
                 questions_to_ask[], notes_for_student[], model, created_at }
    """
    doc.setdefault("created_at", datetime.utcnow())
    result = await mongo["interview_preps"].insert_one(doc)
    return str(result.inserted_id)


async def get_interview_preps_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> list[dict]:
    cursor = mongo["interview_preps"].find({"user_id": user_id}).sort("created_at", -1)
    return [_serialize(doc) async for doc in cursor]


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc
