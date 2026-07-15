"""Feature 8: per-posting tailored resume + cover letter + employer brief.

A student supplies a specific posting either by picking one of their job
leads, by pasting a link (fetched via posting_fetch.py), or by entering the
details manually when fetching fails. One posting-materials agent call
produces the resume variant, cover letter, employer brief, and fit summary,
which are persisted to the MongoDB ``posting_materials`` collection and
never regenerated just to be displayed.
"""

import uuid
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.materials import insert_materials
from app.llm.agents import run_posting_materials_agent
from app.llm.orchestrator import build_posting_materials_context, trim_resume_text
from app.llm.service import get_model
from app.models.lead import JobLead
from app.models.profile import Profile
from app.services import profile_service
from app.services.posting_fetch import fetch_posting


async def generate_materials(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    posting: dict,
    lead_id: str | None = None,
) -> dict:
    """Generate and persist application materials for one posting.

    posting keys: title, employer, description (all required), plus optional
    location and url. Raises ValueError for missing prerequisites and
    RuntimeError when the LLM call fails.
    """
    profile = await profile_service.get_profile(db, user_id)
    if profile is None:
        raise ValueError("Profile not found. Please complete your profile first.")
    if not profile.resume_doc_id:
        raise ValueError("Please upload a resume before generating materials.")
    if not posting.get("description"):
        raise ValueError("Please provide the job description.")

    resume_doc = await mongo["resumes"].find_one(
        {"_id": ObjectId(profile.resume_doc_id)}
    )
    resume_content = {
        "raw_text": trim_resume_text((resume_doc or {}).get("raw_text", "")),
    }

    linkedin_content = None
    if profile.linkedin_doc_id:
        linkedin_doc = await mongo["linkedin"].find_one(
            {"_id": ObjectId(profile.linkedin_doc_id)}
        )
        if linkedin_doc:
            linkedin_content = {
                "raw_text": trim_resume_text(linkedin_doc.get("raw_text", ""))[:2000],
            }

    profile_dict = {
        "degree_level": profile.degree_level.value if profile.degree_level else None,
        "major_program": profile.major_program,
        "track": profile.track.value if profile.track else None,
        "target_roles": [
            {"rank": r.rank, "title": r.title} for r in profile.target_roles
        ],
    }
    context = build_posting_materials_context(
        profile_dict, resume_content, linkedin_content, posting
    )

    result = await run_posting_materials_agent(context)
    if "error" in result:
        raise RuntimeError(result["error"])

    doc = {
        "user_id": str(user_id),
        "lead_id": lead_id,
        "posting": {
            "title": posting.get("title"),
            "employer": posting.get("employer"),
            "location": posting.get("location"),
            "url": posting.get("url"),
            "description": posting.get("description"),
        },
        "fit_summary": result.get("fit_summary", ""),
        "resume_sections": result.get("resume_variant", {}).get("sections", []),
        "cover_letter": result.get("cover_letter", ""),
        "employer_brief": result.get("employer_brief", ""),
        "notes_for_student": result.get("notes_for_student", []),
        "model": get_model(),
        "created_at": datetime.utcnow(),
    }
    doc_id = await insert_materials(mongo, doc)
    doc.pop("_id", None)
    doc["id"] = doc_id
    return doc


async def get_owned_lead(
    db: AsyncSession, user_id: uuid.UUID, lead_id: uuid.UUID
) -> JobLead | None:
    """The lead, only if it belongs to the requesting user."""
    stmt = (
        select(JobLead)
        .join(Profile, JobLead.profile_id == Profile.id)
        .where(Profile.user_id == user_id, JobLead.id == lead_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def generate_for_lead(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    lead: JobLead,
    description: str | None = None,
) -> dict:
    """Generate materials for one of the student's stored job leads.

    The scanner stores only posting metadata, so the description comes either
    from the request body (student pasted it) or a fresh fetch of the
    original posting URL. PostingFetchError propagates so the route can tell
    the student to paste the description manually.
    """
    posting = {
        "title": lead.title,
        "employer": lead.employer,
        "location": None,
        "url": lead.url,
        "description": description,
    }
    if not description:
        fetched = await fetch_posting(lead.url)
        posting["description"] = fetched["description"]
        posting["location"] = fetched.get("location")

    return await generate_materials(db, mongo, user_id, posting, lead_id=str(lead.id))
