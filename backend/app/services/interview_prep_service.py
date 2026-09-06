"""Feature 9: interview prep guidance.

A student asks for prep against one target — either one of their three ranked
target roles or a specific posting (a stored job lead, a pasted link, or
manually entered details). One interview-prep agent call produces the likely
interview formats, focus areas, practice questions, and questions to ask,
which are persisted to the MongoDB ``interview_preps`` collection and never
regenerated just to be displayed.

Unlike Feature 8, a resume is not required: prep is grounded in the student's
resume when there is one, and in their profile and the target otherwise.
"""

import logging
import uuid
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.interview_prep import insert_interview_prep
from app.llm.agents import run_interview_prep_agent
from app.llm.orchestrator import build_interview_prep_context, trim_resume_text
from app.llm.service import get_model
from app.models.lead import JobLead
from app.services import profile_service
from app.services.posting_fetch import PostingFetchError, fetch_posting

logger = logging.getLogger(__name__)


async def _require_profile(db: AsyncSession, user_id: uuid.UUID):
    """The student's profile, which must carry ranked target roles."""
    profile = await profile_service.get_profile(db, user_id)
    if profile is None or not profile.target_roles:
        raise ValueError(
            "Add your ranked target roles before generating interview prep."
        )
    return profile


async def _generate(
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    profile,
    target: dict,
    lead_id: str | None = None,
) -> dict:
    """Run the interview-prep agent for one resolved target and persist it.

    target keys: mode ("role" | "posting"), title, plus optional employer,
    url, rank, and description. Raises RuntimeError when the LLM call fails.
    """
    resume_content = None
    if profile.resume_doc_id:
        resume_doc = await mongo["resumes"].find_one(
            {"_id": ObjectId(profile.resume_doc_id)}
        )
        if resume_doc:
            resume_content = {
                "raw_text": trim_resume_text(resume_doc.get("raw_text", "")),
            }

    profile_dict = {
        "degree_level": profile.degree_level.value if profile.degree_level else None,
        "major_program": profile.major_program,
        "track": profile.track.value if profile.track else None,
        "target_roles": [
            {"rank": r.rank, "title": r.title} for r in profile.target_roles
        ],
    }
    context = build_interview_prep_context(profile_dict, target, resume_content)

    result = await run_interview_prep_agent(context)
    if "error" in result:
        raise RuntimeError(result["error"])

    doc = {
        "user_id": str(user_id),
        "lead_id": lead_id,
        "target": {
            "mode": target["mode"],
            "title": target["title"],
            "employer": target.get("employer"),
            "url": target.get("url"),
            "rank": target.get("rank"),
        },
        "formats": result.get("formats", []),
        "focus_areas": result.get("focus_areas", []),
        "practice_questions": result.get("practice_questions", []),
        "questions_to_ask": result.get("questions_to_ask", []),
        "notes_for_student": result.get("notes_for_student", []),
        "model": get_model(),
        "created_at": datetime.utcnow(),
    }
    doc_id = await insert_interview_prep(mongo, doc)
    doc.pop("_id", None)
    doc["id"] = doc_id
    return doc


async def generate_for_role(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    target_rank: int,
) -> dict:
    """Prep for one of the student's own ranked target roles."""
    profile = await _require_profile(db, user_id)

    role = next((r for r in profile.target_roles if r.rank == target_rank), None)
    if role is None:
        raise ValueError(f"You have no target role ranked {target_rank}.")

    return await _generate(
        mongo,
        user_id,
        profile,
        {"mode": "role", "title": role.title, "rank": role.rank},
    )


async def generate_for_posting(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    posting: dict,
    lead_id: str | None = None,
) -> dict:
    """Prep for one specific posting.

    When the student gave a link but no description, the posting page is
    fetched to enrich the prep. A failed fetch is not fatal here — the title
    and employer alone still support useful guidance — so it is logged and
    the prep runs without the description.
    """
    profile = await _require_profile(db, user_id)

    description = posting.get("description")
    if not description and posting.get("url"):
        try:
            fetched = await fetch_posting(posting["url"])
            description = fetched["description"]
        except PostingFetchError as exc:
            logger.info("Interview-prep posting fetch failed, continuing: %s", exc)
        except Exception:
            # The description is enrichment only, so an unexpected fetch error
            # must never cost the student the quota slot they already spent on
            # a prep the title and employer can still support.
            logger.exception("Unexpected interview-prep posting fetch error")

    return await _generate(
        mongo,
        user_id,
        profile,
        {
            "mode": "posting",
            "title": posting["title"],
            "employer": posting.get("employer"),
            "url": posting.get("url"),
            "description": description,
        },
        lead_id=lead_id,
    )


async def generate_for_lead(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase,
    user_id: uuid.UUID,
    lead: JobLead,
) -> dict:
    """Prep for one of the student's stored job leads."""
    return await generate_for_posting(
        db,
        mongo,
        user_id,
        {"title": lead.title, "employer": lead.employer, "url": lead.url},
        lead_id=str(lead.id),
    )
