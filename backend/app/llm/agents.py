"""Specialized agent functions. Each agent builds the user-turn payload,
calls the LLM service, and parses + validates the JSON response.
The orchestrator decides which agent to call and assembles trimmed context.
"""

import json
import logging
import re

from app.llm import prompts
from app.llm.service import call_llm, FALLBACK_MESSAGE

logger = logging.getLogger(__name__)

ASSESSMENT_MAX_OUTPUT = 2000
RESUME_MAX_OUTPUT = 3000


def _extract_json(raw: str) -> str:
    """Extract the first JSON object from a response that may include code fences or prose."""
    stripped = raw.strip()

    # Check for ```json ... ``` or ``` ... ``` anywhere in the response
    fence_match = re.search(r"```(?:json)?\s*\n([\s\S]*?)\n```", stripped)
    if fence_match:
        return fence_match.group(1).strip()

    # Walk characters to find the first { and its matching }
    start = stripped.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(stripped[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return stripped[start : i + 1]

    return stripped


async def run_assessment_agent(context: dict) -> dict:
    """context keys: degree_level, major_program, track, expected_graduation,
    target_roles (list of titles ranked 1-3), resume_text (trimmed, contact stripped),
    linkedin_summary (optional).
    """
    user_content = json.dumps(context)
    raw = await call_llm(
        prompts.ASSESSMENT_SYSTEM, user_content, max_tokens=ASSESSMENT_MAX_OUTPUT
    )
    if raw is None:
        return {"error": FALLBACK_MESSAGE}
    try:
        result = json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        logger.warning("Assessment agent returned malformed JSON; retrying once")
        raw = await call_llm(
            prompts.ASSESSMENT_SYSTEM, user_content, max_tokens=ASSESSMENT_MAX_OUTPUT
        )
        if raw is None:
            return {"error": FALLBACK_MESSAGE}
        try:
            result = json.loads(_extract_json(raw))
        except json.JSONDecodeError:
            logger.error("Assessment agent: second attempt also malformed")
            return {"error": FALLBACK_MESSAGE}
    return result


async def run_resume_agent(context: dict) -> dict:
    """context keys: profile (structured), resume_content, linkedin_content (optional),
    target_role (dict with title + rank).
    Called once per ranked role — three times total.
    """
    user_content = json.dumps(context)
    raw = await call_llm(
        prompts.RESUME_GENERATION_SYSTEM, user_content, max_tokens=RESUME_MAX_OUTPUT
    )
    if raw is None:
        return {"error": FALLBACK_MESSAGE}
    try:
        result = json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        logger.warning("Resume agent returned malformed JSON; retrying once")
        raw = await call_llm(
            prompts.RESUME_GENERATION_SYSTEM, user_content, max_tokens=RESUME_MAX_OUTPUT
        )
        if raw is None:
            return {"error": FALLBACK_MESSAGE}
        try:
            result = json.loads(_extract_json(raw))
        except json.JSONDecodeError:
            logger.error("Resume agent: second attempt also malformed")
            return {"error": FALLBACK_MESSAGE}
    return result
