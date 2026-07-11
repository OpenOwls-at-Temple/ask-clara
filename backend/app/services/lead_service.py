"""Feature 7: job-leads scanning and matching.

The scan is triggered by the scheduled GitHub Actions workflow via
POST /api/admin/scan-jobs (never by students) and runs as a background task:

1. Fetch postings from the curated Greenhouse/Lever boards (job_sources.py).
2. For each profile with target roles, a deterministic keyword pre-filter
   picks the top candidate postings the student hasn't already been offered.
3. One batched job-match agent call scores those candidates (fit_score 0-1
   + fit_reason). Only new candidates are ever scored, so steady-state LLM
   cost stays small; students with no new candidates cost zero calls.
4. Leads at or above MIN_FIT_SCORE are stored as status='new' rows, which
   drive the in-app notification badge.
"""

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.agents import run_job_match_agent
from app.llm.orchestrator import build_job_match_context
from app.models.lead import JobLead, LeadStatus
from app.models.profile import Profile

logger = logging.getLogger(__name__)

MAX_CANDIDATES_PER_STUDENT = 10  # postings sent to one batched LLM call
MAX_LEADS_PER_SCAN = 5  # new leads stored per student per scan
MIN_FIT_SCORE = 0.55


class AgentFailure(RuntimeError):
    """The job-match LLM call failed for one profile (timeout, malformed output)."""


# Module-level scan state, read by GET /api/admin/scan-jobs/status. The GitHub
# Actions workflow polls it until the background task finishes (the polling
# doubles as keep-alive so Render doesn't spin down mid-scan). In-memory is
# fine: Render runs a single instance and a restart just reads as 'idle'.
_scan_status: dict = {"state": "idle"}


def get_scan_status() -> dict:
    return dict(_scan_status)


def _set_scan_status(**fields) -> None:
    _scan_status.clear()
    _scan_status.update(fields)


_WORD_RE = re.compile(r"[a-z0-9+#]+")

# Generic title words that would otherwise match nearly every posting.
_STOPWORDS = {"of", "and", "the", "a", "an", "in", "for", "to", "at", "i", "ii", "iii"}


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS}


def prefilter_postings(
    postings: list[dict],
    role_titles: list[str],
    limit: int = MAX_CANDIDATES_PER_STUDENT,
) -> list[dict]:
    """Rank postings by keyword overlap with the student's target role titles.

    Cheap and deterministic — its only job is to cut hundreds of postings down
    to a handful worth spending LLM tokens on. The agent does the real scoring.
    """
    role_token_sets = [_tokens(title) for title in role_titles if title]
    role_token_sets = [s for s in role_token_sets if s]
    if not role_token_sets:
        return []

    scored = []
    for posting in postings:
        posting_tokens = _tokens(posting.get("title", ""))
        if not posting_tokens:
            continue
        # Primary: how much of the role title the posting covers.
        # Secondary: how focused the posting title is on that role — breaks
        # ties so "Software Engineer" outranks "Software Engineer Intern"
        # for a "Software Engineer" target.
        best = (0.0, 0.0)
        for role_tokens in role_token_sets:
            hit = len(role_tokens & posting_tokens)
            score = (hit / len(role_tokens), hit / len(posting_tokens))
            best = max(best, score)
        if best[0] > 0:
            scored.append((best, posting))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [posting for _, posting in scored[:limit]]


async def _existing_lead_urls(db: AsyncSession, profile_id: uuid.UUID) -> set[str]:
    result = await db.execute(
        select(JobLead.url).where(JobLead.profile_id == profile_id)
    )
    return set(result.scalars().all())


def _clamp_score(value) -> float | None:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


async def scan_for_profile(
    db: AsyncSession, profile: Profile, postings: list[dict]
) -> int:
    """Match postings for one student and persist new leads.

    Returns leads created; raises AgentFailure if the LLM call fails so the
    scan can count failures instead of silently reporting zero matches.
    """
    role_titles = [r.title for r in profile.target_roles]
    known_urls = await _existing_lead_urls(db, profile.id)
    fresh = [p for p in postings if p["url"] not in known_urls]
    candidates = prefilter_postings(fresh, role_titles)
    if not candidates:
        return 0

    profile_dict = {
        "degree_level": profile.degree_level.value if profile.degree_level else None,
        "major_program": profile.major_program,
        "track": profile.track.value if profile.track else None,
        "target_roles": [
            {"rank": r.rank, "title": r.title} for r in profile.target_roles
        ],
    }
    context = build_job_match_context(profile_dict, candidates)
    result = await run_job_match_agent(context)
    if "error" in result:
        raise AgentFailure(result["error"])

    matches = []
    for match in result.get("matches", []):
        if not isinstance(match, dict):
            continue
        index = match.get("index")
        score = _clamp_score(match.get("fit_score"))
        if not isinstance(index, int) or not 0 <= index < len(candidates):
            continue
        if score is None or score < MIN_FIT_SCORE:
            continue
        matches.append((score, index, str(match.get("fit_reason", ""))))

    matches.sort(reverse=True)
    created = 0
    stored_urls: set[str] = set()
    for score, index, reason in matches[:MAX_LEADS_PER_SCAN]:
        posting = candidates[index]
        if posting["url"] in stored_urls:
            continue
        stored_urls.add(posting["url"])
        db.add(
            JobLead(
                id=uuid.uuid4(),
                profile_id=profile.id,
                source=posting["source"],
                url=posting["url"],
                title=posting["title"],
                employer=posting["employer"],
                fit_score=score,
                fit_reason=reason,
                status=LeadStatus.new,
                found_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        created += 1
    await db.commit()
    return created


async def run_scan(db: AsyncSession, postings: list[dict] | None = None) -> dict:
    """Run the full scan across all profiles with target roles."""
    from app.services.job_sources import fetch_all_postings

    _set_scan_status(state="running", started_at=datetime.now(timezone.utc).isoformat())
    try:
        if postings is None:
            postings = await fetch_all_postings()

        result = await db.execute(
            select(Profile).options(selectinload(Profile.target_roles))
        )
        profiles = [p for p in result.scalars().all() if p.target_roles]

        leads_created = 0
        students_matched = 0
        agent_failures = 0
        for profile in profiles:
            try:
                created = await scan_for_profile(db, profile, postings)
            except AgentFailure as exc:
                # One student's failed match call must not kill the whole scan,
                # but it must be visible in the status — not read as "no fit".
                logger.warning(
                    "Job-match agent failed for profile %s: %s", profile.id, exc
                )
                agent_failures += 1
                continue
            leads_created += created
            if created:
                students_matched += 1

        _set_scan_status(
            state="completed",
            finished_at=datetime.now(timezone.utc).isoformat(),
            postings_fetched=len(postings),
            profiles_scanned=len(profiles),
            students_matched=students_matched,
            leads_created=leads_created,
            agent_failures=agent_failures,
        )
    except Exception as exc:
        logger.exception("Job scan failed")
        _set_scan_status(
            state="failed",
            finished_at=datetime.now(timezone.utc).isoformat(),
            error=str(exc),
        )
    return get_scan_status()


async def list_leads(db: AsyncSession, user_id: uuid.UUID) -> list[JobLead]:
    """The user's leads, best fit first (spec: prioritized by fit)."""
    stmt = (
        select(JobLead)
        .join(Profile, JobLead.profile_id == Profile.id)
        .where(Profile.user_id == user_id)
        .order_by(JobLead.fit_score.desc().nullslast(), JobLead.found_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_lead_status(
    db: AsyncSession, user_id: uuid.UUID, lead_id: uuid.UUID, status: str
) -> JobLead | None:
    """Set one lead's status. Returns None if the lead isn't the user's."""
    stmt = (
        select(JobLead)
        .join(Profile, JobLead.profile_id == Profile.id)
        .where(Profile.user_id == user_id, JobLead.id == lead_id)
    )
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead is None:
        return None
    lead.status = LeadStatus(status)
    await db.commit()
    await db.refresh(lead)
    return lead


async def mark_new_leads_seen(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Flip all of the user's 'new' leads to 'seen' (clears the in-app badge)."""
    stmt = (
        select(JobLead)
        .join(Profile, JobLead.profile_id == Profile.id)
        .where(Profile.user_id == user_id, JobLead.status == LeadStatus.new)
    )
    result = await db.execute(stmt)
    leads = list(result.scalars().all())
    for lead in leads:
        lead.status = LeadStatus.seen
    if leads:
        await db.commit()
    return len(leads)
