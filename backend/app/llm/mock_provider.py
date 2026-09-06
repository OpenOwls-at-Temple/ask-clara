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


def _interview_prep(context: dict) -> dict:
    target = context.get("target") or {}
    title = target.get("title", "Software Engineer")
    return {
        "formats": [
            {
                "name": "Mock format: recruiter screen",
                "what_to_expect": f"Mock expectation: a 30-minute call about your interest in {title}.",
                "how_to_prepare": "Mock prep: rehearse a two-minute background summary.",
            },
            {
                "name": "Mock format: technical screen",
                "what_to_expect": "Mock expectation: one coding problem shared on a live editor.",
                "how_to_prepare": "Mock prep: practice explaining your approach out loud.",
            },
        ],
        "focus_areas": [
            {
                "area": "Mock focus area: data structures",
                "why": f"Mock rationale: core to {title} screens.",
                "how_to_prepare": "Mock prep: work through arrays, hash maps, and trees.",
            }
        ],
        "practice_questions": [
            {
                "question": "Mock question: tell me about a project you shipped end to end.",
                "type": "behavioral",
                "what_they_look_for": "Mock signal: ownership and clear communication.",
            },
            {
                "question": "Mock question: how would you debug a slow API endpoint?",
                "type": "technical",
                "what_they_look_for": "Mock signal: a systematic approach to narrowing causes.",
            },
        ],
        "questions_to_ask": [
            "Mock question to ask: how is success measured in the first six months?"
        ],
        "notes_for_student": [
            "Mock note: book a mock interview with the Temple Career Center."
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
    elif required == {
        "formats",
        "focus_areas",
        "practice_questions",
        "questions_to_ask",
        "notes_for_student",
    }:
        payload = _interview_prep(context)
    else:
        payload = {"note": "Mock response (no known schema requested)."}

    return json.dumps(payload)
