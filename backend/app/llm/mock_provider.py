"""Deterministic, no-network LLM provider for local/CI end-to-end runs.

Returns canned JSON matching the agent schemas in prompts.py. Dispatch keys on
the schema's top-level "required" list so this module never imports prompts
and service.py stays decoupled from prompt definitions. Every string is
prefixed "Mock" so E2E assertions can target it and nobody mistakes the
output for real coaching.
"""

import json


def _context(user_content: str) -> dict:
    """Agents always send json.dumps(context) as the user turn."""
    try:
        parsed = json.loads(user_content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _assessment() -> dict:
    return {
        "strengths": [
            "Mock strength: hands-on Python projects from coursework",
            "Mock strength: campus leadership experience",
        ],
        "gaps": [
            {
                "area": "Mock gap: cloud deployment experience",
                "target_rank": 1,
                "why": "Mock rationale: target roles list AWS as a core skill.",
            }
        ],
        "recommendations": [
            {
                "action": "Mock recommendation: complete an AWS fundamentals course",
                "rationale": "Mock rationale: closes the highest-priority gap.",
            }
        ],
    }


def _resume(context: dict) -> dict:
    target_role = context.get("target_role") or {}
    return {
        "target_rank": target_role.get("rank", 1),
        "target_title": target_role.get("title", "Software Engineer"),
        "sections": [
            {"heading": "Summary", "content": "Mock summary tailored to the role."},
            {
                "heading": "Experience",
                "content": "Mock experience drawn from the uploaded resume.",
            },
        ],
        "notes_for_student": ["Mock note: quantify your project outcomes."],
    }


def _job_match(context: dict) -> dict:
    postings = context.get("postings") or []
    return {
        "matches": [
            {
                "index": p.get("index", i),
                "fit_score": max(0.5, 0.9 - 0.1 * i),
                "fit_reason": "Mock fit: aligns with your ranked target roles.",
            }
            for i, p in enumerate(postings)
        ]
    }


def _plan() -> dict:
    return {
        "horizon_months": 6,
        "items": [
            {
                "skill": "Mock skill: cloud fundamentals",
                "target_rank": 1,
                "why": "Mock rationale: required by your first-choice role.",
            },
            {
                "skill": "Mock skill: technical interviewing",
                "target_rank": 2,
                "why": "Mock rationale: prepares you for recruiting season.",
            },
        ],
    }


def generate(user_content: str, schema: dict | None) -> str:
    """Return canned JSON for the agent identified by the schema shape."""
    required = set((schema or {}).get("required", []))
    context = _context(user_content)

    if required == {"strengths", "gaps", "recommendations"}:
        payload = _assessment()
    elif required == {"target_rank", "target_title", "sections", "notes_for_student"}:
        payload = _resume(context)
    elif required == {"matches"}:
        payload = _job_match(context)
    elif required == {"horizon_months", "items"}:
        payload = _plan()
    else:
        payload = {"note": "Mock response (no known schema requested)."}

    return json.dumps(payload)
