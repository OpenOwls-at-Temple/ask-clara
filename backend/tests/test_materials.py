import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Posting extraction (pure functions, no network)
# ---------------------------------------------------------------------------

LONG_DESCRIPTION = (
    "We are looking for a software engineering intern to join our platform "
    "team. You will build APIs in Python, work with PostgreSQL, and ship "
    "features used by millions of users. Requirements: currently pursuing a "
    "degree in computer science or a related field, familiarity with modern "
    "web frameworks, and strong communication skills. " * 3
)

JSON_LD_PAGE = f"""
<html><head><title>Careers</title>
<script type="application/ld+json">
{{"@context": "https://schema.org", "@type": "JobPosting",
  "title": "Software Engineer Intern",
  "hiringOrganization": {{"@type": "Organization", "name": "Acme"}},
  "jobLocation": {{"@type": "Place",
    "address": {{"@type": "PostalAddress", "addressLocality": "Philadelphia"}}}},
  "description": "<p>{LONG_DESCRIPTION}</p>"}}
</script></head><body><p>Apply now</p></body></html>
"""

PLAIN_PAGE = f"""
<html><head><title>Data Analyst - OtherCo</title>
<script>var tracking = "ignore me";</script></head>
<body><h1>Data Analyst</h1><div>{LONG_DESCRIPTION}</div></body></html>
"""


def test_extract_posting_prefers_json_ld_jobposting():
    from app.services.posting_fetch import extract_posting

    posting = extract_posting(JSON_LD_PAGE, "https://acme.example/jobs/1")
    assert posting["title"] == "Software Engineer Intern"
    assert posting["employer"] == "Acme"
    assert posting["location"] == "Philadelphia"
    assert "software engineering intern" in posting["description"].lower()
    assert "<p>" not in posting["description"]
    assert posting["url"] == "https://acme.example/jobs/1"


def test_extract_posting_falls_back_to_title_and_body_text():
    from app.services.posting_fetch import extract_posting

    posting = extract_posting(PLAIN_PAGE, "https://otherco.example/jobs/2")
    assert posting["title"] == "Data Analyst - OtherCo"
    assert "PostgreSQL" in posting["description"]
    assert "ignore me" not in posting["description"]  # script text excluded


def test_extract_posting_rejects_pages_without_a_readable_posting():
    from app.services.posting_fetch import PostingFetchError, extract_posting

    with pytest.raises(PostingFetchError):
        extract_posting("<html><body>404</body></html>", "https://x.example")


@pytest.mark.asyncio
async def test_fetch_posting_rejects_non_http_and_private_urls():
    from app.services.posting_fetch import PostingFetchError, _validate_url

    with pytest.raises(PostingFetchError):
        await _validate_url("file:///etc/passwd")
    with pytest.raises(PostingFetchError):
        await _validate_url("http://localhost:8000/admin")
    with pytest.raises(PostingFetchError):
        await _validate_url("http://169.254.169.254/latest/meta-data")


# ---------------------------------------------------------------------------
# Posting-materials agent + context builder
# ---------------------------------------------------------------------------

FAKE_MATERIALS_RESPONSE = """{
  "fit_summary": "Your Python projects line up well with this posting.",
  "resume_variant": {"sections": [
    {"heading": "Summary", "content": "Python developer with ML experience."},
    {"heading": "Skills", "content": "Python, FastAPI, PostgreSQL"}
  ]},
  "cover_letter": "Dear Hiring Team, I am excited to apply...",
  "employer_brief": "Acme builds developer tools for data teams.",
  "notes_for_student": ["Consider adding a SQL certification."]
}"""


@pytest.mark.asyncio
async def test_posting_materials_agent_passes_schema_to_llm():
    from app.llm import prompts

    mock = AsyncMock(return_value=FAKE_MATERIALS_RESPONSE)
    with patch("app.llm.agents.call_llm", new=mock):
        from app.llm.agents import run_posting_materials_agent

        result = await run_posting_materials_agent({"posting": {}})
    assert result["fit_summary"].startswith("Your Python projects")
    assert mock.call_args.kwargs["schema"] is prompts.POSTING_MATERIALS_SCHEMA


def test_build_posting_materials_context_caps_description_and_ranks_roles():
    from app.llm.orchestrator import MAX_POSTING_CHARS, build_posting_materials_context

    profile = {
        "degree_level": "undergrad",
        "major_program": "CS",
        "track": "industry",
        "target_roles": [
            {"rank": 2, "title": "Data Analyst"},
            {"rank": 1, "title": "Software Engineer"},
        ],
    }
    context = build_posting_materials_context(
        profile,
        {"raw_text": "Python developer."},
        None,
        {"title": "SWE Intern", "employer": "Acme", "description": "x" * 99_999},
    )
    assert [r["rank"] for r in context["target_roles"]] == [1, 2]
    assert len(context["posting"]["description"]) == MAX_POSTING_CHARS
    assert "email" not in str(context)


# ---------------------------------------------------------------------------
# materials_service unit tests (mocked profile/mongo/LLM)
# ---------------------------------------------------------------------------

VALID_OBJECT_ID = "64a2b3c4d5e6f7890a1b2c3d"

POSTING = {
    "title": "Software Engineer Intern",
    "employer": "Acme",
    "description": "Build APIs in Python.",
    "url": "https://acme.example/jobs/1",
}


def _make_mock_profile(resume_doc_id=VALID_OBJECT_ID):
    profile = MagicMock()
    profile.resume_doc_id = resume_doc_id
    profile.linkedin_doc_id = None
    profile.degree_level.value = "undergrad"
    profile.major_program = "Computer Science"
    profile.track.value = "industry"
    role = MagicMock()
    role.rank = 1
    role.title = "Software Engineer"
    profile.target_roles = [role]
    return profile


def _make_mock_mongo():
    mongo = MagicMock()
    mongo.__getitem__.return_value.find_one = AsyncMock(
        return_value={"raw_text": "Python developer with ML experience."}
    )
    return mongo


@pytest.mark.asyncio
async def test_generate_materials_raises_without_profile_resume_or_description():
    from app.services.materials_service import generate_materials

    with patch(
        "app.services.materials_service.profile_service.get_profile",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError, match="Profile not found"):
            await generate_materials(AsyncMock(), AsyncMock(), uuid.uuid4(), POSTING)

    with patch(
        "app.services.materials_service.profile_service.get_profile",
        new=AsyncMock(return_value=_make_mock_profile(resume_doc_id=None)),
    ):
        with pytest.raises(ValueError, match="resume"):
            await generate_materials(AsyncMock(), AsyncMock(), uuid.uuid4(), POSTING)

    with patch(
        "app.services.materials_service.profile_service.get_profile",
        new=AsyncMock(return_value=_make_mock_profile()),
    ):
        with pytest.raises(ValueError, match="description"):
            await generate_materials(
                AsyncMock(), AsyncMock(), uuid.uuid4(), {**POSTING, "description": ""}
            )


@pytest.mark.asyncio
async def test_generate_materials_persists_and_returns_document():
    from app.services.materials_service import generate_materials

    with (
        patch(
            "app.services.materials_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch(
            "app.llm.agents.call_llm",
            new=AsyncMock(return_value=FAKE_MATERIALS_RESPONSE),
        ),
        patch(
            "app.services.materials_service.insert_materials",
            new=AsyncMock(return_value="materials-id-1"),
        ) as insert,
    ):
        doc = await generate_materials(
            AsyncMock(), _make_mock_mongo(), uuid.uuid4(), POSTING
        )

    assert doc["id"] == "materials-id-1"
    assert doc["fit_summary"].startswith("Your Python projects")
    assert doc["resume_sections"][0]["heading"] == "Summary"
    assert doc["cover_letter"].startswith("Dear Hiring Team")
    assert doc["employer_brief"].startswith("Acme builds")
    assert doc["notes_for_student"] == ["Consider adding a SQL certification."]
    assert insert.await_count == 1


@pytest.mark.asyncio
async def test_generate_materials_raises_runtime_on_llm_failure():
    from app.services.materials_service import generate_materials

    with (
        patch(
            "app.services.materials_service.profile_service.get_profile",
            new=AsyncMock(return_value=_make_mock_profile()),
        ),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(RuntimeError):
            await generate_materials(
                AsyncMock(), _make_mock_mongo(), uuid.uuid4(), POSTING
            )


# ---------------------------------------------------------------------------
# Route integration (real local Postgres via db_session, mocked Mongo + LLM)
# ---------------------------------------------------------------------------


async def _seed_student_with_resume(db_session, generation_count=0):
    from app.models.profile import Profile, TargetRole
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            temple_email=f"{user_id.hex[:8]}@temple.edu",
            display_name="Materials Owner",
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
async def test_student_generates_materials_from_manual_posting(client, db_session):
    user_id, _ = await _seed_student_with_resume(db_session)

    with (
        patch("app.routes.materials.get_mongo_db", return_value=_make_mock_mongo()),
        patch(
            "app.llm.agents.call_llm",
            new=AsyncMock(return_value=FAKE_MATERIALS_RESPONSE),
        ),
        patch(
            "app.services.materials_service.insert_materials",
            new=AsyncMock(return_value="materials-id-1"),
        ),
    ):
        response = await client.post(
            "/api/materials", headers=_auth(user_id), json=POSTING
        )

    assert response.status_code == 200
    body = response.json()
    assert body["fit_summary"]
    assert body["cover_letter"]
    assert body["employer_brief"]
    assert body["posting"]["title"] == "Software Engineer Intern"
    assert body["lead_id"] is None


@pytest.mark.asyncio
async def test_generate_materials_requires_posting_fields(client, db_session):
    user_id, _ = await _seed_student_with_resume(db_session)
    response = await client.post(
        "/api/materials", headers=_auth(user_id), json={"title": "SWE"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_materials_quota_blocks_at_cap_outside_local(client, db_session):
    from app.routes.materials import LLM_GENERATION_CAP

    user_id, _ = await _seed_student_with_resume(
        db_session, generation_count=LLM_GENERATION_CAP
    )
    with patch("app.routes.materials.settings") as mock_settings:
        mock_settings.environment = "staging"
        response = await client.post(
            "/api/materials", headers=_auth(user_id), json=POSTING
        )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_quota_slot_refunded_when_generation_fails(client, db_session):
    from sqlalchemy import select

    from app.models.user import User

    user_id, _ = await _seed_student_with_resume(db_session)

    with (
        patch("app.routes.materials.get_mongo_db", return_value=_make_mock_mongo()),
        patch("app.llm.agents.call_llm", new=AsyncMock(return_value=None)),
    ):
        response = await client.post(
            "/api/materials", headers=_auth(user_id), json=POSTING
        )

    assert response.status_code == 503
    count = (
        (await db_session.execute(select(User).where(User.id == user_id)))
        .scalar_one()
        .llm_generation_count
    )
    assert count == 0


@pytest.mark.asyncio
async def test_student_generates_materials_for_own_lead_with_pasted_description(
    client, db_session
):
    user_id, profile_id = await _seed_student_with_resume(db_session)
    lead_id = await _seed_lead(db_session, profile_id)

    fetch = AsyncMock()
    with (
        patch("app.routes.leads.get_mongo_db", return_value=_make_mock_mongo()),
        patch("app.services.materials_service.fetch_posting", new=fetch),
        patch(
            "app.llm.agents.call_llm",
            new=AsyncMock(return_value=FAKE_MATERIALS_RESPONSE),
        ),
        patch(
            "app.services.materials_service.insert_materials",
            new=AsyncMock(return_value="materials-id-2"),
        ),
    ):
        response = await client.post(
            f"/api/leads/{lead_id}/materials",
            headers=_auth(user_id),
            json={"description": "Build APIs in Python."},
        )

    assert response.status_code == 200
    assert response.json()["lead_id"] == str(lead_id)
    fetch.assert_not_awaited()  # pasted description means no page fetch


@pytest.mark.asyncio
async def test_lead_materials_fetches_posting_when_no_description_given(
    client, db_session
):
    user_id, profile_id = await _seed_student_with_resume(db_session)
    lead_id = await _seed_lead(db_session, profile_id)

    fetched = {**POSTING, "location": "Philadelphia"}
    with (
        patch("app.routes.leads.get_mongo_db", return_value=_make_mock_mongo()),
        patch(
            "app.services.materials_service.fetch_posting",
            new=AsyncMock(return_value=fetched),
        ),
        patch(
            "app.llm.agents.call_llm",
            new=AsyncMock(return_value=FAKE_MATERIALS_RESPONSE),
        ),
        patch(
            "app.services.materials_service.insert_materials",
            new=AsyncMock(return_value="materials-id-3"),
        ),
    ):
        response = await client.post(
            f"/api/leads/{lead_id}/materials", headers=_auth(user_id), json={}
        )

    assert response.status_code == 200
    assert response.json()["posting"]["description"] == POSTING["description"]


@pytest.mark.asyncio
async def test_lead_materials_returns_422_and_refunds_quota_when_fetch_fails(
    client, db_session
):
    from sqlalchemy import select

    from app.models.user import User
    from app.services.posting_fetch import PostingFetchError

    user_id, profile_id = await _seed_student_with_resume(db_session)
    lead_id = await _seed_lead(db_session, profile_id)

    with (
        patch("app.routes.leads.get_mongo_db", return_value=_make_mock_mongo()),
        patch(
            "app.services.materials_service.fetch_posting",
            new=AsyncMock(side_effect=PostingFetchError("Couldn't read the page.")),
        ),
    ):
        response = await client.post(
            f"/api/leads/{lead_id}/materials", headers=_auth(user_id), json={}
        )

    assert response.status_code == 422
    count = (
        (await db_session.execute(select(User).where(User.id == user_id)))
        .scalar_one()
        .llm_generation_count
    )
    assert count == 0


@pytest.mark.asyncio
async def test_student_cannot_generate_materials_for_another_students_lead(
    client, db_session
):
    from app.models.user import User, UserRole

    owner_id, profile_id = await _seed_student_with_resume(db_session)
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

    llm = AsyncMock(return_value=FAKE_MATERIALS_RESPONSE)
    with patch("app.llm.agents.call_llm", new=llm):
        response = await client.post(
            f"/api/leads/{lead_id}/materials",
            headers=_auth(intruder_id),
            json={"description": "Build APIs in Python."},
        )

    assert response.status_code == 404
    llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_materials_returns_only_own_documents(client, db_session):
    user_id, _ = await _seed_student_with_resume(db_session)

    own_doc = {
        "_id": "abc123",
        "user_id": str(user_id),
        "lead_id": None,
        "posting": POSTING,
        "fit_summary": "Good fit.",
        "resume_sections": [],
        "cover_letter": "Dear team,",
        "employer_brief": "Acme builds tools.",
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

    with patch("app.routes.materials.get_mongo_db", return_value=mongo):
        response = await client.get("/api/materials", headers=_auth(user_id))

    assert response.status_code == 200
    assert len(response.json()) == 1
    # The Mongo query is scoped to the requesting user — never unfiltered.
    assert captured_filters == {"user_id": str(user_id)}
