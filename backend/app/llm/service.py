import asyncio
import logging

import anthropic
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_MODEL = "claude-sonnet-4-6"
FALLBACK_MESSAGE = "I couldn't generate that right now — please try again in a moment."

_anthropic_client: anthropic.AsyncAnthropic | None = None


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


async def _call_anthropic(
    system: str, user_content: str, max_tokens: int
) -> str | None:
    client = _get_anthropic_client()
    for attempt in range(2):
        try:
            message = await client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            return message.content[0].text
        except anthropic.APITimeoutError:
            if attempt == 0:
                await asyncio.sleep(2)
            else:
                logger.warning("Anthropic timeout on second attempt")
                return None
        except anthropic.RateLimitError:
            if attempt == 0:
                await asyncio.sleep(5)
            else:
                logger.warning("Anthropic rate limit on second attempt")
                return None
        except Exception:
            logger.exception("Unexpected Anthropic error")
            return None
    return None


async def _call_gemini(system: str, user_content: str, max_tokens: int) -> str | None:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": user_content}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(2):
            try:
                r = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    params={"key": settings.gemini_api_key},
                    json=payload,
                )
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                logger.warning("Gemini %s: %s", r.status_code, r.text)
                if attempt == 0:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning("Gemini attempt %d error: %s", attempt, e)
                if attempt == 0:
                    await asyncio.sleep(2)
    return None


async def _call_deepseek(system: str, user_content: str, max_tokens: int) -> str | None:
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured.")
    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(2):
            try:
                r = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                logger.warning("DeepSeek %s: %s", r.status_code, r.text)
                if attempt == 0:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning("DeepSeek attempt %d error: %s", attempt, e)
                if attempt == 0:
                    await asyncio.sleep(2)
    return None


async def call_llm(
    system: str,
    user_content: str,
    max_tokens: int = 1024,
) -> str | None:
    """Route to the configured LLM provider. Set LLM_PROVIDER in the environment."""
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return await _call_gemini(system, user_content, max_tokens)
    if provider == "deepseek":
        return await _call_deepseek(system, user_content, max_tokens)
    if provider == "anthropic":
        return await _call_anthropic(system, user_content, max_tokens)
    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}'. Valid values: anthropic, gemini, deepseek."
    )
