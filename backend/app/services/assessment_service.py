import uuid

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.assessments import insert_assessment
from app.llm.agents import run_assessment_agent
from app.llm.orchestrator import build_assessment_context
from app.llm.service import MODEL
from app.services import profile_service


async def run_assessment(
    db: AsyncSession, mongo: AsyncIOMotorDatabase, user_id: uuid.UUID
) -> dict:
    """Run the assessment agent and persist the result.

    1. Load profile + resume/LinkedIn text from Postgres + MongoDB.
    2. Trim context (strip contact blocks, cap to ~1500 tokens).
    3. Call the assessment agent.
    4. Persist the result document to MongoDB `assessments` collection.
    5. Return the structured assessment dict.
    """
    profile = await profile_service.get_profile(db, user_id)
    if profile is None:
        raise ValueError("Profile not found. Please complete your profile first.")

    if not profile.resume_doc_id:
        raise ValueError("Please upload a resume before running an assessment.")

    resume_doc = await mongo["resumes"].find_one(
        {"_id": ObjectId(profile.resume_doc_id)}
    )
    resume_text = (resume_doc or {}).get("raw_text", "")

    linkedin_text = None
    if profile.linkedin_doc_id:
        linkedin_doc = await mongo["linkedin"].find_one(
            {"_id": ObjectId(profile.linkedin_doc_id)}
        )
        if linkedin_doc:
            linkedin_text = linkedin_doc.get("raw_text")

    profile_dict = {
        "degree_level": profile.degree_level.value if profile.degree_level else None,
        "major_program": profile.major_program,
        "track": profile.track.value if profile.track else None,
        "expected_graduation": (
            str(profile.expected_graduation) if profile.expected_graduation else ""
        ),
        "target_roles": [
            {"rank": r.rank, "title": r.title} for r in profile.target_roles
        ],
    }
    context = build_assessment_context(profile_dict, resume_text, linkedin_text)

    result = await run_assessment_agent(context)
    if "error" in result:
        raise RuntimeError(result["error"])

    doc = {
        "user_id": str(user_id),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "recommendations": result.get("recommendations", []),
        "model": MODEL,
    }
    doc_id = await insert_assessment(mongo, doc)
    doc.pop("_id", None)
    doc["id"] = doc_id
    return doc


async def generate_resumes(
    db: AsyncSession, mongo: AsyncIOMotorDatabase, user_id: uuid.UUID
) -> list[dict]:
    """Generate three tailored base resumes, one per ranked target role.

    Calls the resume-generation agent for each rank and persists each document
    to MongoDB `resumes` (kind='generated') before returning.
    Write MongoDB documents before any Postgres reference updates.
    """
    raise NotImplementedError
