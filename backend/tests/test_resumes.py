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
    with patch(
        "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_RESUME_RESPONSE)
    ):
        from app.llm.agents import run_resume_agent

        result = await run_resume_agent(
            {
                "profile": {
                    "degree_level": "undergrad",
                    "major_program": "CS",
                    "track": "industry",
                },
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
        patch(
            "app.llm.agents.call_llm", new=AsyncMock(return_value=FAKE_RESUME_RESPONSE)
        ),
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
@pytest.mark.asyncio
async def test_student_cannot_generate_resumes_for_another_student(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from app.models.profile import Profile
    from datetime import datetime
    import uuid

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    user_a = User(
        id=user_a_id,
        temple_email="usera@temple.edu",
        display_name="User A",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    user_b = User(
        id=user_b_id,
        temple_email="userb@temple.edu",
        display_name="User B",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    profile_b = Profile(
        id=uuid.uuid4(),
        user_id=user_b_id,
        degree_level="undergrad",
        major_program="Computer Science",
        updated_at=datetime.utcnow(),
        resume_doc_id="64a2b3c4d5e6f7890a1b2c3d",
    )
    db_session.add(profile_b)
    await db_session.commit()

    token_a = create_access_token(str(user_a_id))
    headers = {"Authorization": f"Bearer {token_a}"}

    response = await client.post("/api/resumes/generate", headers=headers)
    assert response.status_code == 400
    assert "Profile not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_resume_returns_docx(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid
    from unittest.mock import AsyncMock, patch, MagicMock

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email="downloader@temple.edu",
        display_name="Downloader",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    fake_doc = {
        "user_id": str(user_id),
        "target_title": "Software Engineer",
        "sections": [
            {"heading": "Summary", "content": "A skilled engineer."},
            {"heading": "Skills", "content": "Python, FastAPI"},
        ],
        "edited_text": None,
    }

    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=fake_doc)
    mock_mongo = MagicMock()
    mock_mongo.__getitem__ = MagicMock(return_value=mock_collection)

    with patch("app.routes.documents.get_mongo_db", return_value=mock_mongo):
        response = await client.get(
            "/api/resumes/64a2b3c4d5e6f7890a1b2c3d/download?format=docx",
            headers=headers,
        )

    assert response.status_code == 200
    assert (
        "openxmlformats-officedocument.wordprocessingml"
        in response.headers["content-type"]
    )
    assert (
        "clara-resume-software-engineer.docx" in response.headers["content-disposition"]
    )
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_download_resume_blocked_for_wrong_user(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid
    from unittest.mock import AsyncMock, patch, MagicMock

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    user_a = User(
        id=user_a_id,
        temple_email="owner@temple.edu",
        display_name="Owner",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    user_b = User(
        id=user_b_id,
        temple_email="thief@temple.edu",
        display_name="Thief",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    # Document belongs to user_a
    fake_doc = {
        "user_id": str(user_a_id),
        "target_title": "Data Scientist",
        "sections": [],
        "edited_text": None,
    }

    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=fake_doc)
    mock_mongo = MagicMock()
    mock_mongo.__getitem__ = MagicMock(return_value=mock_collection)

    # user_b tries to download user_a's resume
    token_b = create_access_token(str(user_b_id))
    headers_b = {"Authorization": f"Bearer {token_b}"}

    with patch("app.routes.documents.get_mongo_db", return_value=mock_mongo):
        response = await client.get(
            "/api/resumes/64a2b3c4d5e6f7890a1b2c3d/download",
            headers=headers_b,
        )

    assert response.status_code == 404
