import pytest
from pydantic import ValidationError

from app.schemas.profile import ProfileIn, TargetRoleIn


def _make_roles(ranks):
    return [TargetRoleIn(rank=r, title=f"Role {r}") for r in ranks]


def test_profile_accepts_up_to_three_roles():
    p = ProfileIn(target_roles=_make_roles([1, 2, 3]))
    assert len(p.target_roles) == 3


def test_profile_rejects_duplicate_ranks():
    with pytest.raises(ValidationError):
        ProfileIn(target_roles=_make_roles([1, 1, 3]))


def test_profile_rejects_more_than_three_roles():
    with pytest.raises(ValidationError):
        ProfileIn(target_roles=_make_roles([1, 2, 3, 4]))  # rank 4 also invalid


def test_profile_rejects_invalid_degree_level():
    with pytest.raises(ValidationError):
        ProfileIn(degree_level="highschool")


def test_profile_rejects_invalid_track():
    with pytest.raises(ValidationError):
        ProfileIn(track="freelance")


def test_profile_accepts_partial_update_with_no_roles():
    p = ProfileIn(degree_level="undergrad", major_program="Computer Science")
    assert p.target_roles is None
    assert p.degree_level == "undergrad"


@pytest.mark.asyncio
async def test_student_cannot_see_other_students_profile(client, db_session):
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
        major_program="Math",
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile_b)
    await db_session.commit()

    token_a = create_access_token(str(user_a_id))
    headers = {"Authorization": f"Bearer {token_a}"}

    response = await client.get("/api/profile", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_profile_upsert_replaces_target_roles(db_session):
    from app.services.profile_service import upsert_profile
    from app.schemas.profile import ProfileIn, TargetRoleIn
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email="test@temple.edu",
        display_name="Test User",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    data1 = ProfileIn(
        degree_level="undergrad",
        major_program="CS",
        track="industry",
        target_roles=[
            TargetRoleIn(rank=1, title="Software Engineer"),
            TargetRoleIn(rank=2, title="Data Scientist"),
        ]
    )
    profile1 = await upsert_profile(db_session, user_id, data1)
    assert len(profile1.target_roles) == 2
    assert sorted([r.title for r in profile1.target_roles]) == ["Data Scientist", "Software Engineer"]

    data2 = ProfileIn(
        target_roles=[
            TargetRoleIn(rank=1, title="PM"),
        ]
    )
    profile2 = await upsert_profile(db_session, user_id, data2)
    assert len(profile2.target_roles) == 1
    assert profile2.target_roles[0].title == "PM"


def test_profile_accepts_yyyy_mm_expected_graduation():
    from datetime import date
    p = ProfileIn(expected_graduation="2026-05")
    assert p.expected_graduation == date(2026, 5, 1)


def test_profile_accepts_empty_expected_graduation():
    p = ProfileIn(expected_graduation="")
    assert p.expected_graduation is None


@pytest.mark.asyncio
async def test_linkedin_url_stores_empty_raw_text(client, db_session):
    """URL submission must NOT store the URL string as raw_text (it would pollute LLM context)."""
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email="linkedintest@temple.edu",
        display_name="LinkedIn Test",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    captured = {}

    async def fake_insert_linkedin(mongo, doc):
        captured["doc"] = doc
        return "64a2b3c4d5e6f7890a1b2c3d"

    with patch("app.routes.profile.insert_linkedin", side_effect=fake_insert_linkedin), \
         patch("app.routes.profile.profile_service.set_linkedin_doc_id", new=AsyncMock()):
        response = await client.post(
            "/api/profile/linkedin",
            json={"url": "https://linkedin.com/in/test"},
            headers=headers,
        )

    assert response.status_code == 200
    assert captured["doc"]["raw_text"] == ""
    assert captured["doc"]["structured_json"]["url"] == "https://linkedin.com/in/test"


@pytest.mark.asyncio
async def test_linkedin_export_upload_stores_parsed_text(client, db_session):
    """PDF export upload must parse and store the file text as raw_text."""
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid
    from unittest.mock import AsyncMock, patch

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email="liexport@temple.edu",
        display_name="Export Test",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    captured = {}

    async def fake_insert_linkedin(mongo, doc):
        captured["doc"] = doc
        return "64a2b3c4d5e6f7890a1b2c3d"

    fake_pdf_bytes = b"%PDF-1.4 fake"

    with patch("app.routes.profile.insert_linkedin", side_effect=fake_insert_linkedin), \
         patch("app.routes.profile.profile_service.set_linkedin_doc_id", new=AsyncMock()), \
         patch(
             "app.routes.profile.run_in_threadpool",
             new=AsyncMock(return_value="Parsed LinkedIn export text"),
         ):
        response = await client.post(
            "/api/profile/linkedin/upload",
            files={"file": ("linkedin.pdf", fake_pdf_bytes, "application/pdf")},
            headers=headers,
        )

    assert response.status_code == 200
    assert captured["doc"]["raw_text"] == "Parsed LinkedIn export text"
    assert "preview" in response.json()


@pytest.mark.asyncio
async def test_linkedin_export_upload_rejects_invalid_type(client, db_session):
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        temple_email="badtype@temple.edu",
        display_name="Bad Type",
        role=UserRole.student,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/profile/linkedin/upload",
        files={"file": ("linkedin.txt", b"some text", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400
