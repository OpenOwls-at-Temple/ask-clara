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
PLAN_MAX_OUTPUT = 2000
JOB_MATCH_MAX_OUTPUT = 1500


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


async def _call_and_parse(
    system: str,
    user_content: str,
    max_tokens: int,
    agent_name: str,
    schema: dict | None = None,
) -> dict:
    """Call the LLM and parse the JSON response, retrying once on malformed output.

    On the Anthropic path the schema is enforced by the API (structured outputs),
    so the parse always succeeds and the retry never fires; the extraction +
    retry logic below is the fallback for Gemini/DeepSeek.
    """
    raw = await call_llm(system, user_content, max_tokens=max_tokens, schema=schema)
    if raw is None:
        return {"error": FALLBACK_MESSAGE}
    try:
        return json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        logger.warning("%s agent returned malformed JSON; retrying once", agent_name)
        raw = await call_llm(system, user_content, max_tokens=max_tokens, schema=schema)
        if raw is None:
            return {"error": FALLBACK_MESSAGE}
        try:
            return json.loads(_extract_json(raw))
        except json.JSONDecodeError:
            logger.error("%s agent: second attempt also malformed", agent_name)
            return {"error": FALLBACK_MESSAGE}


async def run_assessment_agent(context: dict) -> dict:
    """context keys: degree_level, major_program, track, expected_graduation,
    target_roles (list of titles ranked 1-3), resume_text (trimmed, contact stripped),
    linkedin_summary (optional).
    """
    return await _call_and_parse(
        prompts.ASSESSMENT_SYSTEM,
        json.dumps(context),
        ASSESSMENT_MAX_OUTPUT,
        "Assessment",
        schema=prompts.ASSESSMENT_SCHEMA,
    )


async def run_resume_agent(context: dict) -> dict:
    """context keys: profile (structured), resume_content, linkedin_content (optional),
    target_role (dict with title + rank).
    Called once per ranked role — three times total.
    """
    return await _call_and_parse(
        prompts.RESUME_GENERATION_SYSTEM,
        json.dumps(context),
        RESUME_MAX_OUTPUT,
        "Resume",
        schema=prompts.RESUME_SCHEMA,
    )


async def run_planning_agent(context: dict) -> dict:
    """context keys: degree_level, major_program, track, target_roles
    (list of {rank, title}), assessment (strengths, gaps, recommendations).
    """
    return await _call_and_parse(
        prompts.DEVELOPMENT_PLAN_SYSTEM,
        json.dumps(context),
        PLAN_MAX_OUTPUT,
        "Planning",
        schema=prompts.DEVELOPMENT_PLAN_SCHEMA,
    )


async def run_job_match_agent(context: dict) -> dict:
    """context keys: degree_level, major_program, track, target_roles
    (list of {rank, title}), postings (list of {index, title, employer, location}).
    One batched call scores all candidate postings for one student.
    """
    return await _call_and_parse(
        prompts.JOB_MATCH_SYSTEM,
        json.dumps(context),
        JOB_MATCH_MAX_OUTPUT,
        "JobMatch",
        schema=prompts.JOB_MATCH_SCHEMA,
    )
