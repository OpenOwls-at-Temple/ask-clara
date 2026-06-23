"""Specialized agent functions. Each agent builds the user-turn payload,
calls the LLM service, and parses + validates the JSON response.
The orchestrator decides which agent to call and assembles trimmed context.
"""

import json
import logging

from app.llm import prompts
from app.llm.service import call_llm, FALLBACK_MESSAGE

logger = logging.getLogger(__name__)

# Max input tokens per agent (enforced by the orchestrator before calling here)
ASSESSMENT_MAX_OUTPUT = 600
RESUME_MAX_OUTPUT = 1200


async def run_assessment_agent(context: dict) -> dict:
    """context keys: degree_level, major_program, track, expected_graduation,
    target_roles (list of titles ranked 1-3), resume_text (trimmed, contact stripped),
    linkedin_summary (optional).
    """
    user_content = json.dumps(context)
    raw = await call_llm(prompts.ASSESSMENT_SYSTEM, user_content, max_tokens=ASSESSMENT_MAX_OUTPUT)
    if raw is None:
        return {"error": FALLBACK_MESSAGE}
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Assessment agent returned malformed JSON; retrying once")
        raw = await call_llm(
            prompts.ASSESSMENT_SYSTEM, user_content, max_tokens=ASSESSMENT_MAX_OUTPUT
        )
        if raw is None:
            return {"error": FALLBACK_MESSAGE}
        try:
            result = json.loads(raw)
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
    raw = await call_llm(prompts.RESUME_GENERATION_SYSTEM, user_content, max_tokens=RESUME_MAX_OUTPUT)
    if raw is None:
        return {"error": FALLBACK_MESSAGE}
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Resume agent returned malformed JSON; retrying once")
        raw = await call_llm(
            prompts.RESUME_GENERATION_SYSTEM, user_content, max_tokens=RESUME_MAX_OUTPUT
        )
        if raw is None:
            return {"error": FALLBACK_MESSAGE}
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Resume agent: second attempt also malformed")
            return {"error": FALLBACK_MESSAGE}
    return result
