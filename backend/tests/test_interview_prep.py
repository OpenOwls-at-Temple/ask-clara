import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


FAKE_PREP_RESPONSE = """{
  "formats": [
    {"name": "Technical screen", "what_to_expect": "One coding problem live.",
     "how_to_prepare": "Practice narrating your approach."}
  ],
  "focus_areas": [
    {"area": "Data structures", "why": "Every screen tests them.",
     "how_to_prepare": "Drill arrays, hash maps, and trees."}
  ],
  "practice_questions": [
    {"question": "Tell me about a project you shipped.", "type": "behavioral",
     "what_they_look_for": "Ownership and clear communication."}
  ],
  "questions_to_ask": ["How is success measured in the first six months?"],
  "notes_for_student": ["Book a mock interview with the Career Center."]
}"""

VALID_OBJECT_ID = "64a2b3c4d5e6f7890a1b2c3d"


# ---------------------------------------------------------------------------
# Interview-prep agent + context builder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_interview_prep_agent_passes_schema_to_llm():
    from app.llm import prompts

    mock = AsyncMock(return_value=FAKE_PREP_RESPONSE)
    with patch("app.llm.agents.call_llm", new=mock):
        from app.llm.agents import run_interview_prep_agent

        result = await run_interview_prep_agent({"target": {}})
    assert result["formats"][0]["name"] == "Technical screen"
    assert mock.call_args.kwargs["schema"] is prompts.INTERVIEW_PREP_SCHEMA


def test_build_interview_prep_context_caps_description_and_strips_pii():
    from app.llm.orchestrator import MAX_POSTING_CHARS, build_interview_prep_context

    profile = {
        "degree_level": "undergrad",
        "major_program": "CS",
        "track": "industry",
        "target_roles": [
            {"rank": 2, "title": "Data Analyst"},
            {"rank": 1, "title": "Software Engineer"},
        ],
    }
    context = build_interview_prep_context(
        profile,
        {
            "mode": "posting",
            "title": "SWE Intern",
            "employer": "Acme",
            "description": "x" * 99_999,
        },
        {"raw_text": "Python developer."},
    )
    assert [r["rank"] for r in context["target_roles"]] == [1, 2]
    assert len(context["target"]["description"]) == MAX_POSTING_CHARS
    assert "@temple.edu" not in str(context)
    assert "is_first_gen" not in str(context)


def test_build_interview_prep_context_omits_description_for_a_role_target():
    from app.llm.orchestrator import build_interview_prep_context

    context = build_interview_prep_context(
        {"degree_level": "phd", "track": "academia", "target_roles": []},
        {"mode": "role", "title": "Research Scientist", "rank": 1},
        None,
    )
    assert context["target"]["description"] is None
    assert context["resume_content"] is None


# ---------------------------------------------------------------------------
# interview_prep_service unit tests (mocked profile/mongo/LLM)
# ---------------------------------------------------------------------------


def _make_mock_profile(resume_doc_id=VALID_OBJECT_ID, ranks=(1,)):
    profile = MagicMock()
    profile.resume_doc_id = resume_doc_id
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"
    roles = []
    for rank in ranks:
        role = MagicMock()
        role.rank = rank
        role.title = f"Role {rank}"
        roles.append(role)
    profile.target_roles = roles
    return profile


def _make_mock_mongo():
    mongo = MagicMock()
    mongo.__getitem__.return_value.find_one = AsyncMock(
        return_value={"raw_text": "Python developer with ML experience."}
    )
    return mongo


@pytest.mark.asyncio
async def test_generate_for_role_requires_ranked_target_roles():
    from app.services.interview_prep_service import generate_for_role

    with patch(
        "app.services.interview_prep_service.profile_service.get_profile",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError, match="ranked target roles"):
            await generate_for_role(AsyncMock(), AsyncMock(), uuid.uuid4(), 1)

    with patch(
        "app.services.interview_prep_service.profile_service.get_profile",
        new=AsyncMock(return_value=_make_mock_profile(ranks=(1,))),
    ):
        with pytest.raises(ValueError, match="ranked 3"):
            await generate_for_role(AsyncMock(), AsyncMock(), uuid.uuid4(), 3)


@pytest.mark.asyncio
async def test_generate_for_role_persists_and_returns_document():
    from app.services.interview_prep_service import generate_for_role

    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile(ranks=(1, 2))),
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ),
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-1"),
        ) as insert,
    ):
        doc = await generate_for_role(AsyncMock(), _make_mock_mongo(), uuid.uuid4(), 2)

    assert doc["id"] == "prep-id-1"
    assert doc["target"] == {
        "mode": "role",
        "title": "Role 2",
        "employer": None,
        "url": None,
        "rank": 2,
    }
    assert doc["formats"][0]["name"] == "Technical screen"
    assert doc["practice_questions"][0]["type"] == "behavioral"
    assert doc["questions_to_ask"] == [
        "How is success measured in the first six months?"
    ]
    assert insert.await_count == 1


@pytest.mark.asyncio
async def test_generate_without_a_resume_still_produces_prep():
    """Unlike Feature 8, prep does not require an uploaded resume."""
    from app.services.interview_prep_service import generate_for_role

    mongo = _make_mock_mongo()
    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile(resume_doc_id=None)),
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ) as llm,
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-2"),
        ),
    ):
        doc = await generate_for_role(AsyncMock(), mongo, uuid.uuid4(), 1)

    assert doc["id"] == "prep-id-2"
    mongo.__getitem__.return_value.find_one.assert_not_awaited()
    assert '"resume_content": null' in llm.call_args.args[1]


@pytest.mark.asyncio
async def test_generate_for_posting_fetches_description_from_the_url():
    from app.services.interview_prep_service import generate_for_posting

    fetch = AsyncMock(return_value={"description": "Build APIs in Python."})
    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch("app.services.interview_prep_service.fetch_posting", new=fetch),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ) as llm,
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-3"),
        ),
    ):
        doc = await generate_for_posting(
            AsyncMock(),
            _make_mock_mongo(),
            uuid.uuid4(),
            {"title": "SWE Intern", "employer": "Acme", "url": "https://x.example/1"},
        )

    fetch.assert_awaited_once()
    assert doc["target"]["mode"] == "posting"
    assert "Build APIs in Python." in llm.call_args.args[1]


@pytest.mark.asyncio
async def test_generate_for_posting_continues_when_the_fetch_fails():
    """A dead posting link degrades the prep — it never blocks it."""
    from app.services.interview_prep_service import generate_for_posting
    from app.services.posting_fetch import PostingFetchError

    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.interview_prep_service.fetch_posting",
            new=AsyncMock(side_effect=PostingFetchError("Couldn't read the page.")),
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ),
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-4"),
        ),
    ):
        doc = await generate_for_posting(
            AsyncMock(),
            _make_mock_mongo(),
            uuid.uuid4(),
            {"title": "SWE Intern", "employer": "Acme", "url": "https://x.example/1"},
        )

    assert doc["id"] == "prep-id-4"
    assert doc["target"]["title"] == "SWE Intern"


@pytest.mark.asyncio
async def test_generate_for_posting_survives_an_unexpected_fetch_error():
    """Enrichment only — an unexpected fetch error never costs the quota slot."""
    from app.services.interview_prep_service import generate_for_posting

    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.services.interview_prep_service.fetch_posting",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ),
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-4b"),
        ),
    ):
        doc = await generate_for_posting(
            AsyncMock(),
            _make_mock_mongo(),
            uuid.uuid4(),
            {"title": "SWE Intern", "url": "https://x.example/1"},
        )

    assert doc["id"] == "prep-id-4b"


@pytest.mark.asyncio
async def test_generate_raises_runtime_on_llm_failure():
    from app.services.interview_prep_service import generate_for_role

    with (
        patch(
            "app.services.interview_prep_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(RuntimeError):
            await generate_for_role(AsyncMock(), _make_mock_mongo(), uuid.uuid4(), 1)


# ---------------------------------------------------------------------------
# Route integration (real local Postgres via db_session, mocked Mongo + LLM)
# ---------------------------------------------------------------------------


async def _seed_student(db_session, generation_count=0):
    from app.models.profile import Profile, TargetRole
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            temple_email=f"{user_id.hex[:8]}@temple.edu",
            display_name="Prep Owner",
            role=UserRole.student,
            llm_generation_count=generation_count,
            created_at=datetime.utcnow(),
        )
    )
    await db_session.flush()
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_doc_id=VALID_OBJECT_ID,
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    await db_session.flush()
    db_session.add(
        TargetRole(
            id=uuid.uuid4(),
            profile_id=profile.id,
            rank=1,
            title="Software Engineer",
        )
    )
    await db_session.commit()
    return user_id, profile.id


async def _seed_lead(db_session, profile_id):
    from app.models.lead import JobLead, LeadStatus

    lead = JobLead(
        id=uuid.uuid4(),
        profile_id=profile_id,
        source="greenhouse",
        url="https://acme.example/jobs/1",
        title="Software Engineer Intern",
        employer="Acme",
        status=LeadStatus.seen,
        found_at=datetime.utcnow(),
    )
    db_session.add(lead)
    await db_session.commit()
    return lead.id


def _auth(user_id):
    from app.auth import create_access_token

    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


@pytest.mark.asyncio
async def test_student_generates_prep_for_a_ranked_target_role(client, db_session):
    user_id, _ = await _seed_student(db_session)

    with (
        patch(
            "app.routes.interview_prep.get_mongo_db", return_value=_make_mock_mongo()
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ),
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-1"),
        ),
    ):
        response = await client.post(
            "/api/interview-prep", headers=_auth(user_id), json={"target_rank": 1}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["target"] == {
        "mode": "role",
        "title": "Software Engineer",
        "employer": None,
        "url": None,
        "rank": 1,
    }
    assert body["formats"][0]["what_to_expect"]
    assert body["practice_questions"]
    assert body["lead_id"] is None


@pytest.mark.asyncio
async def test_prep_request_rejects_no_target_and_both_targets(client, db_session):
    user_id, _ = await _seed_student(db_session)

    empty = await client.post("/api/interview-prep", headers=_auth(user_id), json={})
    assert empty.status_code == 422

    both = await client.post(
        "/api/interview-prep",
        headers=_auth(user_id),
        json={"target_rank": 1, "posting": {"title": "SWE Intern"}},
    )
    assert both.status_code == 422


@pytest.mark.asyncio
async def test_prep_quota_blocks_at_cap_outside_local(client, db_session):
    from app.routes.materials import LLM_GENERATION_CAP

    user_id, _ = await _seed_student(db_session, generation_count=LLM_GENERATION_CAP)
    with patch("app.routes.materials.settings") as mock_settings:
        mock_settings.environment = "staging"
        response = await client.post(
            "/api/interview-prep", headers=_auth(user_id), json={"target_rank": 1}
        )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_quota_slot_refunded_when_prep_generation_fails(client, db_session):
    from sqlalchemy import select

    from app.models.user import User

    user_id, _ = await _seed_student(db_session)

    with (
        patch(
            "app.routes.interview_prep.get_mongo_db", return_value=_make_mock_mongo()
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        response = await client.post(
            "/api/interview-prep", headers=_auth(user_id), json={"target_rank": 1}
        )

    assert response.status_code == 503
    count = (
        (await db_session.execute(select(User).where(User.id == user_id)))
        .scalar_one()
        .llm_generation_count
    )
    assert count == 0


@pytest.mark.asyncio
async def test_student_generates_prep_for_own_lead(client, db_session):
    user_id, profile_id = await _seed_student(db_session)
    lead_id = await _seed_lead(db_session, profile_id)

    with (
        patch("app.routes.leads.get_mongo_db", return_value=_make_mock_mongo()),
        patch(
            "app.services.interview_prep_service.fetch_posting",
            new=AsyncMock(return_value={"description": "Build APIs in Python."}),
        ),
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_PREP_RESPONSE)
        ),
        patch(
            "app.services.interview_prep_service.insert_interview_prep",
            new=AsyncMock(return_value="prep-id-5"),
        ),
    ):
        response = await client.post(
            f"/api/leads/{lead_id}/interview-prep", headers=_auth(user_id)
        )

    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"] == str(lead_id)
    assert body["target"]["employer"] == "Acme"


@pytest.mark.asyncio
async def test_student_cannot_generate_prep_for_another_students_lead(
    client, db_session
):
    from app.models.user import User, UserRole

    _, profile_id = await _seed_student(db_session)
    lead_id = await _seed_lead(db_session, profile_id)

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

    llm = AsyncMock(return_value=FAKE_PREP_RESPONSE)
    with patch("app.llm.agents.call_llm", new=llm):
        response = await client.post(
            f"/api/leads/{lead_id}/interview-prep", headers=_auth(intruder_id)
        )

    assert response.status_code == 404
    llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_interview_preps_returns_only_own_documents(client, db_session):
    user_id, _ = await _seed_student(db_session)

    own_doc = {
        "_id": "abc123",
        "user_id": str(user_id),
        "lead_id": None,
        "target": {"mode": "role", "title": "Software Engineer", "rank": 1},
        "formats": [],
        "focus_areas": [],
        "practice_questions": [],
        "questions_to_ask": [],
        "notes_for_student": [],
        "model": "claude-sonnet-4-6",
        "created_at": datetime.utcnow(),
    }

    captured_filters = {}

    def find(query):
        captured_filters.update(query)
        cursor = MagicMock()
        cursor.sort.return_value.__aiter__.return_value = [dict(own_doc)]
        return cursor

    mongo = MagicMock()
    mongo.__getitem__.return_value.find = find

    with patch("app.routes.interview_prep.get_mongo_db", return_value=mongo):
        response = await client.get("/api/interview-prep", headers=_auth(user_id))

    assert response.status_code == 200
    assert len(response.json()) == 1
    # The Mongo query is scoped to the requesting user — never unfiltered.
    assert captured_filters == {"user_id": str(user_id)}


@pytest.mark.asyncio
async def test_mock_provider_returns_prep_matching_the_schema():
    from app.llm import mock_provider, prompts

    import json

    payload = json.loads(
        mock_provider.generate(
            json.dumps({"target": {"title": "Data Analyst"}}),
            prompts.INTERVIEW_PREP_SCHEMA,
        )
    )
    assert set(payload) == set(prompts.INTERVIEW_PREP_SCHEMA["required"])
    assert payload["practice_questions"][0]["type"] == "behavioral"
