import asyncio
import logging

import anthropic
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
FALLBACK_MESSAGE = "I couldn't generate that right now — please try again in a moment."

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key is not configured.")
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def call_gemini(
    system: str,
    user_content: str,
    max_tokens: int = 1024,
) -> str | None:
    """Call Google's Gemini API via direct HTTP POST request."""
    model = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {"Content-Type": "application/json"}
    params = {"key": settings.gemini_api_key}

    payload = {
        "contents": [{"parts": [{"text": user_content}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        },
    }

    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(2):
            try:
                r = await client.post(url, headers=headers, params=params, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text
                else:
                    logger.warning(
                        f"Gemini API returned status code {r.status_code}: {r.text}"
                    )
                    if attempt == 0:
                        await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Error calling Gemini on attempt {attempt}: {e}")
                if attempt == 0:
                    await asyncio.sleep(2)
        return None


async def call_llm(
    system: str,
    user_content: str,
    max_tokens: int = 1024,
) -> str | None:
    """Call the configured LLM API (Gemini or Anthropic) with automatic retry.

    Returns the raw text response, or None if attempts fail.
    """
    if settings.gemini_api_key:
        return await call_gemini(system, user_content, max_tokens)

    if not settings.anthropic_api_key:
        logger.error(
            "No LLM API keys configured! Set GEMINI_API_KEY or ANTHROPIC_API_KEY in .env."
        )
        return None

    client = _get_client()
    for attempt in range(2):
        try:
            message = await client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            return message.content[0].text
        except anthropic.APITimeoutError:
            if attempt == 0:
                await asyncio.sleep(2)
            else:
                logger.warning("LLM timeout on second attempt")
                return None
        except anthropic.RateLimitError:
            if attempt == 0:
                await asyncio.sleep(5)
            else:
                logger.warning("LLM rate limit on second attempt")
                return None
        except Exception:
            logger.exception("Unexpected LLM error")
            return None
    return None
