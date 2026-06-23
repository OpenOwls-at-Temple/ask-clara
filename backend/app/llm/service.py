import asyncio
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
FALLBACK_MESSAGE = "I couldn't generate that right now — please try again in a moment."

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def call_llm(
    system: str,
    user_content: str,
    max_tokens: int = 1024,
) -> str | None:
    """Call the Anthropic API with one automatic retry on timeout or rate-limit.

    Returns the raw text response, or None if both attempts fail.
    Callers are responsible for JSON parsing and validation.
    """
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
