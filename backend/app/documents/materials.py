from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


async def insert_materials(mongo: AsyncIOMotorDatabase, doc: dict) -> str:
    """Insert a posting-materials document and return its string _id.

    doc shape: { user_id, lead_id (optional), posting: {title, employer,
                 location, url, description}, fit_summary, resume_sections[],
                 cover_letter, employer_brief, notes_for_student[], model,
                 created_at }
    """
    doc.setdefault("created_at", datetime.utcnow())
    result = await mongo["posting_materials"].insert_one(doc)
    return str(result.inserted_id)


async def get_materials_for_user(
    mongo: AsyncIOMotorDatabase, user_id: str
) -> list[dict]:
    cursor = (
        mongo["posting_materials"].find({"user_id": user_id}).sort("created_at", -1)
    )
    return [_serialize(doc) async for doc in cursor]


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc
