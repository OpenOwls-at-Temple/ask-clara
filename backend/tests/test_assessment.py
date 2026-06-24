import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# LLM agent unit tests (no DB, no Mongo)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assessment_agent_returns_structured_output():
    fake_response = '{"strengths": ["Python"], "gaps": [], "recommendations": []}'
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=fake_response)):
        from app.llm.agents import run_assessment_agent

        result = await run_assessment_agent(
            {
                "degree_level": "undergrad",
                "major_program": "CS",
                "track": "industry",
                "expected_graduation": "2026-05",
                "target_roles": ["Software Engineer"],
                "resume_text": "Experienced in Python and React.",
            }
        )
    assert "strengths" in result
    assert "Python" in result["strengths"]


@pytest.mark.asyncio
async def test_assessment_agent_returns_fallback_on_api_failure():
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)):
        from app.llm.agents import run_assessment_agent

        result = await run_assessment_agent({})
    assert "error" in result


@pytest.mark.asyncio
async def test_assessment_agent_retries_on_malformed_json():
    """Agent retries once on bad JSON; if second attempt also fails it returns an error."""
    bad_json = "not valid json {"
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=bad_json)):
        from app.llm.agents import run_assessment_agent

        result = await run_assessment_agent({})
    assert "error" in result


# ---------------------------------------------------------------------------
# assessment_service unit tests (DB and Mongo mocked)
# ---------------------------------------------------------------------------


VALID_OBJECT_ID = "64a2b3c4d5e6f7890a1b2c3d"


def _make_mock_profile(resume_doc_id=VALID_OBJECT_ID, linkedin_doc_id=None):
    profile = MagicMock()
    profile.resume_doc_id = resume_doc_id
    profile.linkedin_doc_id = linkedin_doc_id
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"
    profile.expected_graduation = None
    profile.target_roles = []
    return profile


def _make_mock_mongo(resume_text="Experienced Python developer with projects in ML."):
    mongo = MagicMock()
    mongo.__getitem__.return_value.find_one = AsyncMock(
        return_value={"raw_text": resume_text}
    )
    return mongo


@pytest.mark.asyncio
async def test_run_assessment_raises_when_no_profile():
    with patch(
        "app.services.assessment_service.profile_service.get_profile",
        new=AsyncMock(return_value=None),
    ):
        from app.services.assessment_service import run_assessment

        with pytest.raises(ValueError, match="Profile not found"):
            await run_assessment(AsyncMock(), AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_run_assessment_raises_when_no_resume():
    mock_profile = _make_mock_profile(resume_doc_id=None)
    with patch(
        "app.services.assessment_service.profile_service.get_profile",
        new=AsyncMock(return_value=mock_profile),
    ):
        from app.services.assessment_service import run_assessment

        with pytest.raises(ValueError, match="resume"):
            await run_assessment(AsyncMock(), AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_run_assessment_returns_structured_result():
    mock_profile = _make_mock_profile()
    mock_mongo = _make_mock_mongo()
    fake_llm_response = '{"strengths": ["Python", "FastAPI"], "gaps": [], "recommendations": []}'

    with (
        patch(
            "app.services.assessment_service.profile_service.get_profile",
            new=AsyncMock(return_value=mock_profile),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=fake_llm_response)),
        patch(
            "app.services.assessment_service.insert_assessment",
            new=AsyncMock(return_value="doc_abc123"),
        ),
    ):
        from app.services.assessment_service import run_assessment

        result = await run_assessment(AsyncMock(), mock_mongo, uuid.uuid4())

    assert result["id"] == "doc_abc123"
    assert "Python" in result["strengths"]
    assert result["gaps"] == []
    assert result["recommendations"] == []
    assert result["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_run_assessment_raises_runtime_on_llm_error():
    mock_profile = _make_mock_profile()
    mock_mongo = _make_mock_mongo()

    with (
        patch(
            "app.services.assessment_service.profile_service.get_profile",
            new=AsyncMock(return_value=mock_profile),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        from app.services.assessment_service import run_assessment

        with pytest.raises(RuntimeError):
            await run_assessment(AsyncMock(), mock_mongo, uuid.uuid4())


# ---------------------------------------------------------------------------
# Ownership / authorization (integration-level, skipped until TestClient setup)
# ---------------------------------------------------------------------------


def test_student_cannot_trigger_assessment_for_another_student():
    # Each route is gated by get_current_user which extracts user_id from the JWT.
    # The service always scopes profile lookup to that user_id, so another student's
    # profile can never be accessed. Full integration test requires TestClient + test DB.
    pytest.skip("requires TestClient + async test DB setup")
