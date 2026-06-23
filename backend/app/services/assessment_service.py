import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase


async def run_assessment(
    db: AsyncSession, mongo: AsyncIOMotorDatabase, user_id: uuid.UUID
) -> dict:
    """Run the assessment agent and persist the result.

    1. Load profile + resume/LinkedIn text from Postgres + MongoDB.
    2. Trim context (strip contact blocks, cap to ~1500 tokens).
    3. Call the LLM orchestrator with the assessment agent.
    4. Persist the result document to MongoDB `assessments` collection.
    5. Return the structured assessment dict.
    """
    raise NotImplementedError


async def generate_resumes(
    db: AsyncSession, mongo: AsyncIOMotorDatabase, user_id: uuid.UUID
) -> list[dict]:
    """Generate three tailored base resumes, one per ranked target role.

    Calls the resume-generation agent for each rank and persists each document
    to MongoDB `resumes` (kind='generated') before returning.
    Write MongoDB documents before any Postgres reference updates.
    """
    raise NotImplementedError
