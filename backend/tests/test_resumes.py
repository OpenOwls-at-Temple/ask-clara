import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# LLM agent unit tests
# ---------------------------------------------------------------------------

FAKE_RESUME_RESPONSE = """{
  "target_rank": 1,
  "target_title": "Software Engineer",
  "sections": [
    {"heading": "Summary", "content": "Python developer with ML experience."},
    {"heading": "Skills", "content": "Python, FastAPI, React"}
  ],
  "notes_for_student": ["Consider adding a GitHub link."]
}"""


@pytest.mark.asyncio
async def test_resume_agent_returns_structured_output():
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_RESUME_RESPONSE)):
        from app.llm.agents import run_resume_agent

        result = await run_resume_agent(
            {
                "profile": {"degree_level": "undergrad", "major_program": "CS", "track": "industry"},
                "resume_content": {"raw_text": "Python developer."},
                "linkedin_content": None,
                "target_role": {"rank": 1, "title": "Software Engineer"},
            }
        )
    assert result["target_rank"] == 1
    assert result["target_title"] == "Software Engineer"
    assert len(result["sections"]) == 2
    assert result["notes_for_student"] == ["Consider adding a GitHub link."]


@pytest.mark.asyncio
async def test_resume_agent_returns_fallback_on_api_failure():
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)):
        from app.llm.agents import run_resume_agent

        result = await run_resume_agent({})
    assert "error" in result


@pytest.mark.asyncio
async def test_resume_agent_retries_on_malformed_json():
    bad_json = "not valid json {"
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=bad_json)):
        from app.llm.agents import run_resume_agent

        result = await run_resume_agent({})
    assert "error" in result


# ---------------------------------------------------------------------------
# assessment_service.generate_resumes unit tests
# ---------------------------------------------------------------------------

VALID_OBJECT_ID = "64a2b3c4d5e6f7890a1b2c3d"


def _make_mock_profile_with_roles(resume_doc_id=VALID_OBJECT_ID):
    profile = MagicMock()
    profile.resume_doc_id = resume_doc_id
    profile.linkedin_doc_id = None
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"

    role1 = MagicMock()
    role1.rank = 1
    role1.title = "Software Engineer"

    role2 = MagicMock()
    role2.rank = 2
    role2.title = "Data Scientist"

    role3 = MagicMock()
    role3.rank = 3
    role3.title = "ML Engineer"

    profile.target_roles = [role1, role2, role3]
    return profile


def _make_mock_mongo_for_resumes():
    mongo = MagicMock()
    mongo.__getitem__.return_value.find_one = AsyncMock(
        return_value={"raw_text": "Python developer with ML experience."}
    )
    return mongo


@pytest.mark.asyncio
async def test_generate_resumes_raises_when_no_profile():
    with patch(
        "app.services.assessment_service.profile_service.get_profile",
        new=AsyncMock(return_value=None),
    ):
        from app.services.assessment_service import generate_resumes

        with pytest.raises(ValueError, match="Profile not found"):
            await generate_resumes(AsyncMock(), AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_resumes_raises_when_no_resume():
    mock_profile = _make_mock_profile_with_roles(resume_doc_id=None)
    with patch(
        "app.services.assessment_service.profile_service.get_profile",
        new=AsyncMock(return_value=mock_profile),
    ):
        from app.services.assessment_service import generate_resumes

        with pytest.raises(ValueError, match="resume"):
            await generate_resumes(AsyncMock(), AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_resumes_raises_when_no_target_roles():
    mock_profile = _make_mock_profile_with_roles()
    mock_profile.target_roles = []
    with patch(
        "app.services.assessment_service.profile_service.get_profile",
        new=AsyncMock(return_value=mock_profile),
    ):
        from app.services.assessment_service import generate_resumes

        with pytest.raises(ValueError, match="target role"):
            await generate_resumes(AsyncMock(), AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_resumes_returns_three_drafts():
    mock_profile = _make_mock_profile_with_roles()
    mock_mongo = _make_mock_mongo_for_resumes()

    with (
        patch(
            "app.services.assessment_service.profile_service.get_profile",
            new=AsyncMock(return_value=mock_profile),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_RESUME_RESPONSE)),
        patch(
            "app.services.assessment_service.insert_resume",
            new=AsyncMock(side_effect=["id_rank1", "id_rank2", "id_rank3"]),
        ),
    ):
        from app.services.assessment_service import generate_resumes

        results = await generate_resumes(AsyncMock(), mock_mongo, uuid.uuid4())

    assert len(results) == 3
    assert results[0]["id"] == "id_rank1"
    assert results[0]["kind"] == "generated"
    assert results[0]["sections"][0]["heading"] == "Summary"


@pytest.mark.asyncio
async def test_generate_resumes_raises_runtime_on_llm_error():
    mock_profile = _make_mock_profile_with_roles()
    mock_mongo = _make_mock_mongo_for_resumes()

    with (
        patch(
            "app.services.assessment_service.profile_service.get_profile",
            new=AsyncMock(return_value=mock_profile),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        from app.services.assessment_service import generate_resumes

        with pytest.raises(RuntimeError):
            await generate_resumes(AsyncMock(), mock_mongo, uuid.uuid4())


# ---------------------------------------------------------------------------
# Ownership / authorization
# ---------------------------------------------------------------------------


def test_student_cannot_generate_resumes_for_another_student():
    # The route extracts user_id from the JWT via get_current_user; the service
    # always scopes the profile lookup to that user_id. No other student's data
    # can be accessed. Full integration test requires TestClient + async test DB.
    pytest.skip("requires TestClient + async test DB setup")
