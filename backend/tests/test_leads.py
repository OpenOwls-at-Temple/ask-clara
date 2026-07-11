import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Job source normalization (pure functions, no network)
# ---------------------------------------------------------------------------


def test_normalize_greenhouse_extracts_postings():
    from app.services.job_sources import normalize_greenhouse

    payload = {
        "jobs": [
            {
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
                "title": "  Software Engineer Intern ",
                "location": {"name": "Philadelphia, PA"},
            },
            {"absolute_url": None, "title": "Broken entry"},
        ]
    }
    postings = normalize_greenhouse("Acme", payload)
    assert len(postings) == 1
    assert postings[0] == {
        "source": "greenhouse",
        "url": "https://boards.greenhouse.io/acme/jobs/1",
        "title": "Software Engineer Intern",
        "employer": "Acme",
        "location": "Philadelphia, PA",
    }


def test_normalize_lever_extracts_postings():
    from app.services.job_sources import normalize_lever

    payload = [
        {
            "hostedUrl": "https://jobs.lever.co/acme/abc",
            "text": "Data Analyst",
            "categories": {"location": "Remote"},
        },
        {"hostedUrl": "https://jobs.lever.co/acme/def", "text": None},
    ]
    postings = normalize_lever("Acme", payload)
    assert len(postings) == 1
    assert postings[0]["source"] == "lever"
    assert postings[0]["location"] == "Remote"


def test_normalize_lever_tolerates_non_list_payload():
    from app.services.job_sources import normalize_lever

    assert normalize_lever("Acme", {"error": "not found"}) == []


# ---------------------------------------------------------------------------
# Deterministic pre-filter
# ---------------------------------------------------------------------------


def _posting(title, url=None):
    return {
        "source": "greenhouse",
        "url": url or f"https://example.com/{title.replace(' ', '-').lower()}",
        "title": title,
        "employer": "Acme",
        "location": "Remote",
    }


def test_prefilter_ranks_by_title_overlap():
    from app.services.lead_service import prefilter_postings

    postings = [
        _posting("Accountant"),
        _posting("Software Engineer Intern"),
        _posting("Software Engineer"),
        _posting("Marketing Manager"),
    ]
    result = prefilter_postings(postings, ["Software Engineer"], limit=2)
    titles = [p["title"] for p in result]
    assert "Software Engineer" in titles
    assert "Marketing Manager" not in titles
    assert "Accountant" not in titles
    assert len(result) == 2
    # Exact match outranks partial match
    assert titles[0] == "Software Engineer"


def test_prefilter_matches_any_of_the_ranked_roles():
    from app.services.lead_service import prefilter_postings

    postings = [_posting("Data Scientist"), _posting("Chef")]
    result = prefilter_postings(postings, ["Software Engineer", "Data Scientist"])
    assert [p["title"] for p in result] == ["Data Scientist"]


def test_prefilter_returns_empty_without_roles():
    from app.services.lead_service import prefilter_postings

    assert prefilter_postings([_posting("Software Engineer")], []) == []


# ---------------------------------------------------------------------------
# Job-match agent + context builder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_job_match_agent_passes_schema_to_llm():
    from app.llm import prompts

    fake = '{"matches": [{"index": 0, "fit_score": 0.9, "fit_reason": "Strong fit"}]}'
    mock = AsyncMock(return_value=fake)
    with patch("app.llm.agents.call_llm", new=mock):
        from app.llm.agents import run_job_match_agent

        result = await run_job_match_agent({"postings": []})
    assert result["matches"][0]["fit_score"] == 0.9
    assert mock.call_args.kwargs["schema"] is prompts.JOB_MATCH_SCHEMA


def test_build_job_match_context_sends_no_pii():
    from app.llm.orchestrator import build_job_match_context

    profile = {
        "degree_level": "undergrad",
        "major_program": "CS",
        "track": "industry",
        "target_roles": [
            {"rank": 2, "title": "Data Analyst"},
            {"rank": 1, "title": "Software Engineer"},
        ],
    }
    postings = [_posting("Software Engineer Intern")]
    context = build_job_match_context(profile, postings)

    assert [r["rank"] for r in context["target_roles"]] == [1, 2]
    assert context["postings"][0]["index"] == 0
    assert context["postings"][0]["employer"] == "Acme"
    # Only posting metadata goes to the model — no URL, no student identifiers
    assert "url" not in context["postings"][0]
    assert "email" not in str(context)


# ---------------------------------------------------------------------------
# scan_for_profile (DB mocked via db_session integration below; agent mocked)
# ---------------------------------------------------------------------------


def _make_scan_profile():
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"
    role = MagicMock()
    role.rank = 1
    role.title = "Software Engineer"
    profile.target_roles = [role]
    return profile


def test_clamp_score():
    from app.services.lead_service import _clamp_score

    assert _clamp_score(0.7) == 0.7
    assert _clamp_score(1.4) == 1.0
    assert _clamp_score(-1) == 0.0
    assert _clamp_score("0.5") == 0.5
    assert _clamp_score("high") is None
    assert _clamp_score(None) is None


# ---------------------------------------------------------------------------
# Full scan + student endpoints (integration, real local Postgres)
# ---------------------------------------------------------------------------


async def _seed_student(db_session, title="Software Engineer"):
    from app.models.profile import Profile, TargetRole
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email=f"{user_id.hex[:8]}@temple.edu",
        display_name="Lead Owner",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(id=uuid.uuid4(), user_id=user_id, updated_at=datetime.utcnow())
    db_session.add(profile)
    await db_session.flush()
    db_session.add(
        TargetRole(id=uuid.uuid4(), profile_id=profile.id, rank=1, title=title)
    )
    await db_session.commit()
    return user_id, profile.id


_MATCH_RESPONSE = '{"matches": [{"index": 0, "fit_score": 0.9, "fit_reason": "Matches your rank-1 role"}]}'


@pytest.mark.asyncio
async def test_scan_for_profile_creates_leads_and_skips_known_urls(db_session):
    """Per-profile scan (run_scan iterates this over every profile — tested
    per-profile so the local dev DB's real profiles can't skew counts)."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.profile import Profile
    from app.services.lead_service import scan_for_profile

    _, profile_id = await _seed_student(db_session)
    profile = (
        await db_session.execute(
            select(Profile)
            .where(Profile.id == profile_id)
            .options(selectinload(Profile.target_roles))
        )
    ).scalar_one()
    postings = [_posting("Software Engineer Intern", url="https://example.com/se-1")]

    llm = AsyncMock(return_value=_MATCH_RESPONSE)
    with patch("app.llm.agents.call_llm", new=llm):
        created = await scan_for_profile(db_session, profile, postings)
    assert created == 1
    assert llm.await_count == 1

    # Second scan with the same postings: URL already stored → no candidates,
    # no LLM call, no duplicate lead.
    with patch("app.llm.agents.call_llm", new=llm):
        created = await scan_for_profile(db_session, profile, postings)
    assert created == 0
    assert llm.await_count == 1  # unchanged — model was not re-called


@pytest.mark.asyncio
async def test_run_scan_drops_low_fit_matches(db_session):
    from app.services.lead_service import run_scan

    await _seed_student(db_session)
    low_fit = '{"matches": [{"index": 0, "fit_score": 0.2, "fit_reason": "Weak"}]}'
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=low_fit)):
        status = await run_scan(db_session, postings=[_posting("Software Engineer")])
    assert status["leads_created"] == 0


@pytest.mark.asyncio
async def test_run_scan_reports_failed_state_on_error(db_session):
    from app.services import lead_service

    with patch.object(
        lead_service, "run_job_match_agent", new=AsyncMock(side_effect=None)
    ):
        with patch(
            "app.services.job_sources.fetch_all_postings",
            new=AsyncMock(side_effect=RuntimeError("boards unreachable")),
        ):
            status = await lead_service.run_scan(db_session)
    assert status["state"] == "failed"
    assert "boards unreachable" in status["error"]


@pytest.mark.asyncio
async def test_student_sees_own_leads_best_fit_first(client, db_session):
    from app.auth import create_access_token
    from app.services.lead_service import run_scan

    user_id, _ = await _seed_student(db_session)
    two_matches = (
        '{"matches": ['
        '{"index": 0, "fit_score": 0.6, "fit_reason": "Decent"},'
        '{"index": 1, "fit_score": 0.95, "fit_reason": "Excellent"}]}'
    )
    postings = [
        _posting("Software Engineer", url="https://example.com/a"),
        _posting("Software Engineer Intern", url="https://example.com/b"),
    ]
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=two_matches)):
        await run_scan(db_session, postings=postings)

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}
    response = await client.get("/api/leads", headers=headers)
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) == 2
    assert leads[0]["fit_score"] >= leads[1]["fit_score"]
    assert all(lead["status"] == "new" for lead in leads)


@pytest.mark.asyncio
async def test_student_cannot_see_or_update_another_students_leads(client, db_session):
    from app.auth import create_access_token
    from app.services.lead_service import run_scan
    from app.models.user import User, UserRole

    owner_id, _ = await _seed_student(db_session)
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=_MATCH_RESPONSE)):
        await run_scan(db_session, postings=[_posting("Software Engineer")])

    intruder_id = uuid.uuid4()
    db_session.add(
        User(
            id=intruder_id,
            temple_email=f"{intruder_id.hex[:8]}@temple.edu",
            display_name="Intruder",
            role=UserRole.student,
            created_at=datetime.utcnow(),
        )
    )
    await db_session.commit()

    owner_headers = {"Authorization": f"Bearer {create_access_token(str(owner_id))}"}
    intruder_headers = {
        "Authorization": f"Bearer {create_access_token(str(intruder_id))}"
    }

    response = await client.get("/api/leads", headers=intruder_headers)
    assert response.status_code == 200
    assert response.json() == []

    lead_id = (await client.get("/api/leads", headers=owner_headers)).json()[0]["id"]
    response = await client.patch(
        f"/api/leads/{lead_id}", headers=intruder_headers, json={"status": "dismissed"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_student_can_update_lead_status_and_mark_seen(client, db_session):
    from app.auth import create_access_token
    from app.services.lead_service import run_scan

    user_id, _ = await _seed_student(db_session)
    with patch("app.llm.agents.call_llm", new=AsyncMock(return_value=_MATCH_RESPONSE)):
        await run_scan(db_session, postings=[_posting("Software Engineer")])

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}

    # mark-seen clears the in-app notification badge
    response = await client.post("/api/leads/mark-seen", headers=headers)
    assert response.status_code == 200
    assert response.json()["updated"] == 1

    lead = (await client.get("/api/leads", headers=headers)).json()[0]
    assert lead["status"] == "seen"

    response = await client.patch(
        f"/api/leads/{lead['id']}", headers=headers, json={"status": "applied"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "applied"

    # "new" is system-assigned — students cannot set it
    response = await client.patch(
        f"/api/leads/{lead['id']}", headers=headers, json={"status": "new"}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Admin trigger endpoints (shared-secret machine-to-machine auth)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scan_trigger_rejects_missing_or_wrong_secret(client):
    with patch("app.routes.admin.settings") as mock_settings:
        mock_settings.scan_trigger_secret = "right-secret"

        response = await client.post("/api/admin/scan-jobs")
        assert response.status_code == 401

        response = await client.post(
            "/api/admin/scan-jobs", headers={"X-Scan-Trigger-Secret": "wrong"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_scan_trigger_returns_503_when_unconfigured(client):
    with patch("app.routes.admin.settings") as mock_settings:
        mock_settings.scan_trigger_secret = None
        response = await client.post(
            "/api/admin/scan-jobs", headers={"X-Scan-Trigger-Secret": "anything"}
        )
        assert response.status_code == 503


@pytest.mark.asyncio
async def test_scan_trigger_accepts_valid_secret_and_starts_background_task(client):
    with (
        patch("app.routes.admin.settings") as mock_settings,
        patch("app.routes.admin._run_scan_task", new=AsyncMock()) as task,
        patch(
            "app.routes.admin.lead_service.get_scan_status",
            return_value={"state": "idle"},
        ),
    ):
        mock_settings.scan_trigger_secret = "right-secret"
        response = await client.post(
            "/api/admin/scan-jobs", headers={"X-Scan-Trigger-Secret": "right-secret"}
        )
    assert response.status_code == 202
    assert response.json() == {"status": "started"}
    task.assert_awaited()


@pytest.mark.asyncio
async def test_scan_trigger_conflicts_while_running(client):
    with (
        patch("app.routes.admin.settings") as mock_settings,
        patch(
            "app.routes.admin.lead_service.get_scan_status",
            return_value={"state": "running"},
        ),
    ):
        mock_settings.scan_trigger_secret = "right-secret"
        response = await client.post(
            "/api/admin/scan-jobs", headers={"X-Scan-Trigger-Secret": "right-secret"}
        )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_scan_status_requires_secret(client):
    with patch("app.routes.admin.settings") as mock_settings:
        mock_settings.scan_trigger_secret = "right-secret"

        response = await client.get("/api/admin/scan-jobs/status")
        assert response.status_code == 401

        response = await client.get(
            "/api/admin/scan-jobs/status",
            headers={"X-Scan-Trigger-Secret": "right-secret"},
        )
        assert response.status_code == 200
        assert "state" in response.json()
