import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_assessment_agent_returns_structured_output():
    fake_response = '{"strengths": ["Python"], "gaps": [], "recommendations": []}'
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=fake_response)):
        from app.llm.agents import run_assessment_agent
        result = await run_assessment_agent({
            "degree_level": "undergrad",
            "major_program": "CS",
            "track": "industry",
            "expected_graduation": "2026-05",
            "target_roles": ["Software Engineer"],
            "resume_text": "Experienced in Python and React.",
        })
    assert "strengths" in result
    assert "Python" in result["strengths"]


@pytest.mark.asyncio
async def test_assessment_agent_returns_fallback_on_api_failure():
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)):
        from app.llm.agents import run_assessment_agent
        result = await run_assessment_agent({})
    assert "error" in result


def test_student_cannot_trigger_assessment_for_another_student():
    # TODO: set up two authenticated users; assert user A cannot POST /api/assessment as user B
    pytest.skip("not implemented")
