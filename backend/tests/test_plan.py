import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# LLM agent unit tests (no DB, no Mongo)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_planning_agent_returns_structured_output():
    fake_response = (
        '{"horizon_months": 6, "items": ['
        '{"skill": "Learn SQL", "why": "Required for data roles", "target_rank": 1}]}'
    )
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=fake_response)):
        from app.llm.agents import run_planning_agent

        result = await run_planning_agent(
            {
                "degree_level": "undergrad",
                "major_program": "CS",
                "track": "industry",
                "target_roles": [{"rank": 1, "title": "Data Analyst"}],
                "assessment": {"strengths": [], "gaps": [], "recommendations": []},
            }
        )
    assert result["horizon_months"] == 6
    assert result["items"][0]["skill"] == "Learn SQL"


@pytest.mark.asyncio
async def test_planning_agent_returns_fallback_on_api_failure():
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)):
        from app.llm.agents import run_planning_agent

        result = await run_planning_agent({})
    assert "error" in result


@pytest.mark.asyncio
async def test_planning_agent_retries_on_malformed_json():
    """Agent retries once on bad JSON; if second attempt also fails it returns an error."""
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value="not json {")):
        from app.llm.agents import run_planning_agent

        result = await run_planning_agent({})
    assert "error" in result


# ---------------------------------------------------------------------------
# Orchestrator context builder
# ---------------------------------------------------------------------------


def test_build_plan_context_orders_roles_and_trims_assessment():
    from app.llm.orchestrator import build_plan_context

    profile = {
        "degree_level": "phd",
        "major_program": "Bioinformatics",
        "track": "academia",
        "target_roles": [
            {"rank": 2, "title": "Data Scientist"},
            {"rank": 1, "title": "Research Scientist"},
        ],
    }
    assessment = {
        "id": "abc",
        "user_id": "should-not-be-sent",
        "strengths": ["Publications"],
        "gaps": [],
        "recommendations": [],
        "model": "claude-sonnet-4-6",
    }
    context = build_plan_context(profile, assessment)

    assert [r["rank"] for r in context["target_roles"]] == [1, 2]
    assert context["assessment"] == {
        "strengths": ["Publications"],
        "gaps": [],
        "recommendations": [],
    }
    # No identifiers or metadata leak into the model context
    assert "user_id" not in str(context)


# ---------------------------------------------------------------------------
# plan_service unit tests (DB and Mongo mocked)
# ---------------------------------------------------------------------------


def _make_mock_profile(with_roles=True):
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"
    role = MagicMock()
    role.rank = 1
    role.title = "Software Engineer"
    profile.target_roles = [role] if with_roles else []
    return profile


def _make_mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_generate_plan_raises_when_no_profile():
    with patch(
        "app.services.plan_service.profile_service.get_profile",
        new=AsyncMock(return_value=None),
    ):
        from app.services.plan_service import generate_plan

        with pytest.raises(ValueError, match="Profile not found"):
            await generate_plan(_make_mock_db(), MagicMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_plan_raises_when_no_target_roles():
    with patch(
        "app.services.plan_service.profile_service.get_profile",
        new=AsyncMock(return_value=_make_mock_profile(with_roles=False)),
    ):
        from app.services.plan_service import generate_plan

        with pytest.raises(ValueError, match="target roles"):
            await generate_plan(_make_mock_db(), MagicMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_plan_raises_when_no_assessment():
    with (
        patch(
            "app.services.plan_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.plan_service.get_latest_assessment_for_user",
            new=AsyncMock(return_value=None),
        ),
    ):
        from app.services.plan_service import generate_plan

        with pytest.raises(ValueError, match="assessment"):
            await generate_plan(_make_mock_db(), MagicMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_plan_injects_pending_status_into_items():
    fake_llm_response = (
        '{"horizon_months": 6, "items": ['
        '{"skill": "Build a REST API project", "why": "Shows backend skills", "target_rank": 1},'
        '{"skill": "AWS certification", "why": "Cloud skills gap", "target_rank": "2"}]}'
    )
    db = _make_mock_db()
    with (
        patch(
            "app.services.plan_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.plan_service.get_latest_assessment_for_user",
            new=AsyncMock(
                return_value={"strengths": [], "gaps": [], "recommendations": []}
            ),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=fake_llm_response)),
    ):
        from app.services.plan_service import generate_plan

        plan = await generate_plan(db, MagicMock(), uuid.uuid4())

    assert plan.horizon_months == 6
    assert len(plan.items) == 2
    assert all(item["status"] == "pending" for item in plan.items)
    assert plan.items[1]["target_rank"] == 2  # string rank coerced to int
    db.add.assert_called_once()
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_generate_plan_raises_runtime_on_llm_error():
    with (
        patch(
            "app.services.plan_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.plan_service.get_latest_assessment_for_user",
            new=AsyncMock(
                return_value={"strengths": [], "gaps": [], "recommendations": []}
            ),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        from app.services.plan_service import generate_plan

        with pytest.raises(RuntimeError):
            await generate_plan(_make_mock_db(), MagicMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_generate_plan_raises_runtime_on_empty_items():
    with (
        patch(
            "app.services.plan_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.plan_service.get_latest_assessment_for_user",
            new=AsyncMock(
                return_value={"strengths": [], "gaps": [], "recommendations": []}
            ),
        ),
        patch(
            "app.llm.agents.call_llm",
            new=AsyncMock(return_value='{"horizon_months": 6, "items": []}'),
        ),
    ):
        from app.services.plan_service import generate_plan

        with pytest.raises(RuntimeError):
            await generate_plan(_make_mock_db(), MagicMock(), uuid.uuid4())


def test_coerce_rank_and_horizon():
    from app.services.plan_service import _coerce_horizon, _coerce_rank

    assert _coerce_rank(1) == 1
    assert _coerce_rank("3") == 3
    assert _coerce_rank(7) is None
    assert _coerce_rank(None) is None
    assert _coerce_horizon(6) == 6
    assert _coerce_horizon("12") == 12
    assert _coerce_horizon(None) == 6
    assert _coerce_horizon(99) == 6


# ---------------------------------------------------------------------------
# Ownership / authorization (integration-level, real local Postgres)
# ---------------------------------------------------------------------------


async def _seed_user_with_plan(db_session):
    from app.models.plan import DevelopmentPlan
    from app.models.profile import Profile
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email=f"{user_id.hex[:8]}@temple.edu",
        display_name="Plan Owner",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(id=uuid.uuid4(), user_id=user_id, updated_at=datetime.utcnow())
    db_session.add(profile)
    await db_session.flush()

    plan = DevelopmentPlan(
        id=uuid.uuid4(),
        profile_id=profile.id,
        horizon_months=6,
        created_at=datetime.utcnow(),
        items=[
            {
                "skill": "Learn Docker",
                "why": "Deployment",
                "target_rank": 1,
                "status": "pending",
            }
        ],
    )
    db_session.add(plan)
    await db_session.commit()
    return user_id, plan.id


@pytest.mark.asyncio
async def test_student_can_mark_own_plan_item_complete(client, db_session):
    from app.auth import create_access_token

    user_id, plan_id = await _seed_user_with_plan(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}

    response = await client.patch(
        f"/api/plan/{plan_id}/items/0", headers=headers, json={"status": "complete"}
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "complete"

    # And the latest-plan endpoint reflects the persisted change
    response = await client.get("/api/plan", headers=headers)
    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "complete"


@pytest.mark.asyncio
async def test_student_cannot_update_another_students_plan(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole

    owner_id, plan_id = await _seed_user_with_plan(db_session)

    intruder_id = uuid.uuid4()
    intruder = User(
        id=intruder_id,
        temple_email=f"{intruder_id.hex[:8]}@temple.edu",
        display_name="Intruder",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(intruder)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(str(intruder_id))}"}
    response = await client.patch(
        f"/api/plan/{plan_id}/items/0", headers=headers, json={"status": "complete"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_plan_item_rejects_out_of_range_index(client, db_session):
    from app.auth import create_access_token

    user_id, plan_id = await _seed_user_with_plan(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}

    response = await client.patch(
        f"/api/plan/{plan_id}/items/5", headers=headers, json={"status": "complete"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_plan_returns_null_when_none_exists(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email=f"{user_id.hex[:8]}@temple.edu",
        display_name="No Plan Yet",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}
    response = await client.get("/api/plan", headers=headers)
    assert response.status_code == 200
    assert response.json() is None
