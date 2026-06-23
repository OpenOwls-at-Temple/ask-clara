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
        r"\S+@\S+\.\S+",           # email
        r"\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}",  # phone
        r"\d+\s+\w+\s+(St|Ave|Rd|Blvd|Dr|Lane|Way)",  # street address
    ]
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    cleaned_lines = [line for line in text.splitlines() if not combined.search(line)]
    return "\n".join(cleaned_lines)


def trim_resume_text(text: str) -> str:
    """Strip PII and cap length before any LLM call."""
    text = strip_contact_block(text)
    return text[:MAX_INPUT_CHARS]


def build_assessment_context(profile: dict, resume_text: str, linkedin_text: str | None) -> dict:
    """Assemble the minimal context dict for the assessment agent."""
    return {
        "degree_level": profile.get("degree_level"),
        "major_program": profile.get("major_program"),
        "track": profile.get("track"),
        "expected_graduation": str(profile.get("expected_graduation") or ""),
        "target_roles": [r["title"] for r in sorted(profile.get("target_roles", []), key=lambda r: r["rank"])],
        "resume_text": trim_resume_text(resume_text),
        "linkedin_summary": trim_resume_text(linkedin_text)[:2000] if linkedin_text else None,
    }


def build_resume_context(profile: dict, resume_content: dict, linkedin_content: dict | None, target_role: dict) -> dict:
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
