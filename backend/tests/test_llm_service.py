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


def _assert_matches_schema(value, schema):
    """Minimal structural validator (no jsonschema dependency in the repo)."""
    t = schema.get("type")
    if t == "object":
        assert isinstance(value, dict)
        for key in schema.get("required", []):
            assert key in value, f"missing required key: {key}"
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                _assert_matches_schema(value[key], sub)
    elif t == "array":
        assert isinstance(value, list)
        for item in value:
            _assert_matches_schema(item, schema.get("items", {}))
    elif t == "string":
        assert isinstance(value, str)
    elif t == "integer":
        assert isinstance(value, int)
        if "enum" in schema:
            assert value in schema["enum"]
    elif t == "number":
        assert isinstance(value, (int, float))


@pytest.mark.asyncio
async def test_mock_provider_output_matches_every_agent_schema(monkeypatch):
    import json

    from app.llm import prompts

    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    monkeypatch.setattr(service.settings, "environment", "local")

    cases = [
        (prompts.ASSESSMENT_SCHEMA, {"degree_level": "undergrad"}),
        (prompts.RESUME_SCHEMA, {"target_role": {"rank": 2, "title": "Data Analyst"}}),
        (prompts.JOB_MATCH_SCHEMA, {"postings": [{"index": 0}, {"index": 1}]}),
        (prompts.DEVELOPMENT_PLAN_SCHEMA, {"target_roles": []}),
    ]
    for schema, context in cases:
        raw = await service.call_llm("sys", json.dumps(context), schema=schema)
        _assert_matches_schema(json.loads(raw), schema)


@pytest.mark.asyncio
async def test_mock_provider_echoes_the_requested_target_role(monkeypatch):
    import json

    from app.llm import prompts

    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    monkeypatch.setattr(service.settings, "environment", "local")

    raw = await service.call_llm(
        "sys",
        json.dumps({"target_role": {"rank": 3, "title": "Product Manager"}}),
        schema=prompts.RESUME_SCHEMA,
    )
    data = json.loads(raw)
    assert data["target_rank"] == 3
    assert data["target_title"] == "Product Manager"


@pytest.mark.asyncio
async def test_mock_provider_scores_one_match_per_posting(monkeypatch):
    import json

    from app.llm import prompts

    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    monkeypatch.setattr(service.settings, "environment", "local")

    raw = await service.call_llm(
        "sys",
        json.dumps({"postings": [{"index": 0}, {"index": 1}, {"index": 2}]}),
        schema=prompts.JOB_MATCH_SCHEMA,
    )
    matches = json.loads(raw)["matches"]
    assert [m["index"] for m in matches] == [0, 1, 2]


@pytest.mark.asyncio
async def test_mock_provider_refuses_outside_local_environment(monkeypatch):
    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    monkeypatch.setattr(service.settings, "environment", "staging")
    with pytest.raises(RuntimeError, match="local"):
        await service.call_llm("sys", "{}")


def test_get_model_reports_mock_provider(monkeypatch):
    monkeypatch.setattr(service.settings, "llm_provider", "mock")
    assert service.get_model() == "mock"
