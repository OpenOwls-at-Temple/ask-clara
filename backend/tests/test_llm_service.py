"""Retry and fallback behavior of the provider-switchable LLM client.

All provider APIs are mocked — these tests must never hit a real model API.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import httpx
import pytest

from app.llm import service


def _timeout_error() -> anthropic.APITimeoutError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APITimeoutError(request=request)


def _rate_limit_error() -> anthropic.RateLimitError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(429, request=request)
    return anthropic.RateLimitError("rate limited", response=response, body=None)


def _message(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    message = MagicMock()
    message.content = [block]
    return message


def _client_with(side_effect) -> MagicMock:
    client = MagicMock()
    client.messages.create = AsyncMock(side_effect=side_effect)
    return client


@pytest.mark.asyncio
async def test_anthropic_retries_after_timeout_then_succeeds(monkeypatch):
    client = _client_with([_timeout_error(), _message("ok")])
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: client)

    with patch("app.llm.service.asyncio.sleep", new=AsyncMock()):
        result = await service._call_anthropic("system", "user", 100)

    assert result == "ok"
    assert client.messages.create.await_count == 2


@pytest.mark.asyncio
async def test_anthropic_returns_none_after_two_timeouts(monkeypatch):
    client = _client_with([_timeout_error(), _timeout_error()])
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: client)

    with patch("app.llm.service.asyncio.sleep", new=AsyncMock()):
        result = await service._call_anthropic("system", "user", 100)

    assert result is None
    assert client.messages.create.await_count == 2


@pytest.mark.asyncio
async def test_anthropic_returns_none_after_two_rate_limits(monkeypatch):
    client = _client_with([_rate_limit_error(), _rate_limit_error()])
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: client)

    with patch("app.llm.service.asyncio.sleep", new=AsyncMock()):
        result = await service._call_anthropic("system", "user", 100)

    assert result is None
    assert client.messages.create.await_count == 2


@pytest.mark.asyncio
async def test_anthropic_unexpected_error_does_not_retry(monkeypatch):
    client = _client_with(RuntimeError("boom"))
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: client)

    result = await service._call_anthropic("system", "user", 100)

    assert result is None
    assert client.messages.create.await_count == 1


@pytest.mark.asyncio
async def test_anthropic_passes_schema_as_structured_output(monkeypatch):
    client = _client_with([_message("{}")])
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: client)
    schema = {"type": "object", "properties": {}}

    await service._call_anthropic("system", "user", 100, schema=schema)

    kwargs = client.messages.create.await_args.kwargs
    assert kwargs["output_config"] == {
        "format": {"type": "json_schema", "schema": schema}
    }


@pytest.mark.asyncio
async def test_call_llm_routes_to_configured_provider(monkeypatch):
    monkeypatch.setattr(service.settings, "llm_provider", "anthropic")
    with patch.object(
        service, "_call_anthropic", new=AsyncMock(return_value="from-anthropic")
    ) as mock_call:
        result = await service.call_llm("sys", "user", max_tokens=50)
    assert result == "from-anthropic"
    mock_call.assert_awaited_once_with("sys", "user", 50, schema=None)

    monkeypatch.setattr(service.settings, "llm_provider", "gemini")
    with patch.object(
        service, "_call_gemini", new=AsyncMock(return_value="from-gemini")
    ):
        assert await service.call_llm("sys", "user") == "from-gemini"

    monkeypatch.setattr(service.settings, "llm_provider", "deepseek")
    with patch.object(
        service, "_call_deepseek", new=AsyncMock(return_value="from-deepseek")
    ):
        assert await service.call_llm("sys", "user") == "from-deepseek"


@pytest.mark.asyncio
async def test_call_llm_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(service.settings, "llm_provider", "openai")
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        await service.call_llm("sys", "user")


def test_get_model_follows_provider(monkeypatch):
    monkeypatch.setattr(service.settings, "llm_provider", "anthropic")
    assert service.get_model() == service.settings.anthropic_model
    monkeypatch.setattr(service.settings, "llm_provider", "gemini")
    assert service.get_model() == service.settings.gemini_model
    monkeypatch.setattr(service.settings, "llm_provider", "deepseek")
    assert service.get_model() == service.settings.deepseek_model
