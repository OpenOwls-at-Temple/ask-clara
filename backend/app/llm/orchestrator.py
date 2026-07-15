"""Orchestrator: selects the right agent, assembles trimmed context,
and enforces the per-call token budget.
"""

import re

# Hard cap on resume/LinkedIn text sent per call (~1500 tokens ≈ 6000 chars)
MAX_INPUT_CHARS = 6000
MAX_EXPERIENCE_BLOCKS = 3


def strip_contact_block(text: str) -> str:
    """Remove lines that look like contact info (email, phone, address)."""
    patterns = [
        r"\S+@\S+\.\S+",  # email
        r"\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}",  # phone
        # street address, allowing multi-word names ("1801 N Broad St")
        r"\d+\s+(?:\w+\s+){1,4}(St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Lane|Ln|Way|Ct|Court)\.?\b",
    ]
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    cleaned_lines = [line for line in text.splitlines() if not combined.search(line)]
    return "\n".join(cleaned_lines)


def trim_resume_text(text: str) -> str:
    """Strip PII and cap length before any LLM call."""
    text = strip_contact_block(text)
    return text[:MAX_INPUT_CHARS]


def build_assessment_context(
    profile: dict, resume_text: str, linkedin_text: str | None
) -> dict:
    """Assemble the minimal context dict for the assessment agent."""
    return {
        "degree_level": profile.get("degree_level"),
        "major_program": profile.get("major_program"),
        "track": profile.get("track"),
        "expected_graduation": str(profile.get("expected_graduation") or ""),
        "target_roles": [
            r["title"]
            for r in sorted(profile.get("target_roles", []), key=lambda r: r["rank"])
        ],
        "resume_text": trim_resume_text(resume_text),
        "linkedin_summary": (
            trim_resume_text(linkedin_text)[:2000] if linkedin_text else None
        ),
    }


def build_plan_context(profile: dict, assessment: dict) -> dict:
    """Assemble the minimal context dict for the development-plan agent.

    The saved assessment already excludes PII; completed plan items and
    raw resume text are deliberately not sent.
    """
    return {
        "degree_level": profile.get("degree_level"),
        "major_program": profile.get("major_program"),
        "track": profile.get("track"),
        "target_roles": [
            {"rank": r["rank"], "title": r["title"]}
            for r in sorted(profile.get("target_roles", []), key=lambda r: r["rank"])
        ],
        "assessment": {
            "strengths": assessment.get("strengths", []),
            "gaps": assessment.get("gaps", []),
            "recommendations": assessment.get("recommendations", []),
        },
    }


def build_job_match_context(profile: dict, postings: list[dict]) -> dict:
    """Assemble the minimal context dict for the job-match agent.

    Sends only profile basics + ranked role titles + posting metadata —
    no PII, no resume text (matching is against stated goals, not the resume).
    """
    return {
        "degree_level": profile.get("degree_level"),
        "major_program": profile.get("major_program"),
        "track": profile.get("track"),
        "target_roles": [
            {"rank": r["rank"], "title": r["title"]}
            for r in sorted(profile.get("target_roles", []), key=lambda r: r["rank"])
        ],
        "postings": [
            {
                "index": i,
                "title": p.get("title"),
                "employer": p.get("employer"),
                "location": p.get("location"),
            }
            for i, p in enumerate(postings)
        ],
    }


def build_resume_context(
    profile: dict,
    resume_content: dict,
    linkedin_content: dict | None,
    target_role: dict,
) -> dict:
    """Assemble context for a single resume-generation call (one target role)."""
    return {
        "profile": {
            "degree_level": profile.get("degree_level"),
            "major_program": profile.get("major_program"),
            "track": profile.get("track"),
        },
        "resume_content": resume_content,
        "linkedin_content": linkedin_content,
        "target_role": target_role,
    }
