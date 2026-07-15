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
        ],
    )
    profile1 = await upsert_profile(db_session, user_id, data1)
    assert len(profile1.target_roles) == 2
    assert sorted([r.title for r in profile1.target_roles]) == [
        "Data Scientist",
        "Software Engineer",
    ]

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

    with patch(
        "app.services.profile_service.insert_linkedin",
        side_effect=fake_insert_linkedin,
    ), patch("app.services.profile_service.set_linkedin_doc_id", new=AsyncMock()):
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

    with patch(
        "app.services.profile_service.insert_linkedin",
        side_effect=fake_insert_linkedin,
    ), patch(
        "app.services.profile_service.set_linkedin_doc_id", new=AsyncMock()
    ), patch(
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


def test_parse_csv_export_flattens_rows_to_readable_text():
    """LinkedIn's data export is CSV — rows become 'Header: value' blocks."""
    from app.routes.profile import _parse_csv_export

    csv_bytes = (
        b"Company Name,Title,Started On,Finished On,Description\n"
        b"Acme,Software Intern,Jun 2024,Aug 2024,Built APIs in Python\n"
        b'OtherCo,"Data Analyst",Jan 2025,,"Analyzed data, wrote SQL"\n'
    )
    text = _parse_csv_export(csv_bytes)
    assert "Company Name: Acme" in text
    assert "Title: Software Intern" in text
    assert "Description: Analyzed data, wrote SQL" in text
    # Empty cells (Finished On for OtherCo) are omitted, not "Finished On:"
    assert "Finished On: \n" not in text


@pytest.mark.asyncio
async def test_linkedin_export_upload_accepts_csv(client, db_session):
    """The LinkedIn data export produces CSVs — they must parse and store."""
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid
    from unittest.mock import AsyncMock, patch

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            temple_email="csvexport@temple.edu",
            display_name="CSV Export",
            role=UserRole.student,
            created_at=datetime.utcnow(),
        )
    )
    await db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}
    csv_bytes = b"Company Name,Title\nAcme,Software Intern\n"
    with patch(
        "app.routes.profile.profile_service.upsert_linkedin_with_consistency", return_value="64a2b3c4d5e6f7890a1b2c3d"
    ) as mock_upsert:
        response = await client.post(
            "/api/profile/linkedin/upload",
            files={"file": ("Positions.csv", csv_bytes, "text/csv")},
            headers=headers,
        )

    assert response.status_code == 200
    assert "Company Name: Acme" in mock_upsert.call_args.kwargs["raw_text"]
    assert "Title: Software Intern" in mock_upsert.call_args.kwargs["raw_text"]


@pytest.mark.asyncio
async def test_resume_upload_still_rejects_csv(client, db_session):
    """CSV is a LinkedIn-export format only — the resume endpoint stays PDF/DOCX."""
    from app.auth import create_access_token
    from app.models.user import User, UserRole
    from datetime import datetime
    import uuid

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            temple_email="csvresume@temple.edu",
            display_name="CSV Resume",
            role=UserRole.student,
            created_at=datetime.utcnow(),
        )
    )
    await db_session.commit()

    headers = {"Authorization": f"Bearer {create_access_token(str(user_id))}"}
    response = await client.post(
        "/api/profile/resume",
        files={"file": ("resume.csv", b"a,b\n1,2\n", "text/csv")},
        headers=headers,
    )
    assert response.status_code == 400


def _fake_mongo(inserted_id="507f1f77bcf86cd799439011"):
    from unittest.mock import AsyncMock, MagicMock

    collection = MagicMock()
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=inserted_id))
    collection.delete_one = AsyncMock()
    mongo = MagicMock()
    mongo.__getitem__.return_value = collection
    return mongo, collection


@pytest.mark.asyncio
async def test_resume_upsert_deletes_mongo_doc_when_postgres_write_fails(monkeypatch):
    """The Mongo document must not be orphaned if the Postgres link fails."""
    import uuid
    from unittest.mock import AsyncMock
    from bson import ObjectId

    from app.services import profile_service

    mongo, collection = _fake_mongo()
    monkeypatch.setattr(profile_service, "get_profile", AsyncMock(return_value=None))
    monkeypatch.setattr(
        profile_service,
        "set_resume_doc_id",
        AsyncMock(side_effect=RuntimeError("postgres down")),
    )

    with pytest.raises(RuntimeError):
        await profile_service.upsert_resume_with_consistency(
            None, mongo, uuid.uuid4(), raw_text="some resume text"
        )

    collection.delete_one.assert_awaited_once_with(
        {"_id": ObjectId("507f1f77bcf86cd799439011")}
    )


@pytest.mark.asyncio
async def test_resume_upsert_deletes_old_doc_on_success(monkeypatch):
    import uuid
    from unittest.mock import AsyncMock, MagicMock
    from bson import ObjectId

    from app.services import profile_service

    old_doc_id = "64a2b3c4d5e6f7890a1b2c3d"
    mongo, collection = _fake_mongo()
    profile = MagicMock(resume_doc_id=old_doc_id)
    monkeypatch.setattr(profile_service, "get_profile", AsyncMock(return_value=profile))
    monkeypatch.setattr(profile_service, "set_resume_doc_id", AsyncMock())

    doc_id = await profile_service.upsert_resume_with_consistency(
        None, mongo, uuid.uuid4(), raw_text="new resume text"
    )

    assert doc_id == "507f1f77bcf86cd799439011"
    collection.delete_one.assert_awaited_once_with({"_id": ObjectId(old_doc_id)})


@pytest.mark.asyncio
async def test_linkedin_upsert_deletes_mongo_doc_when_postgres_write_fails(monkeypatch):
    import uuid
    from unittest.mock import AsyncMock
    from bson import ObjectId

    from app.services import profile_service

    mongo, collection = _fake_mongo()
    monkeypatch.setattr(profile_service, "get_profile", AsyncMock(return_value=None))
    monkeypatch.setattr(
        profile_service,
        "set_linkedin_doc_id",
        AsyncMock(side_effect=RuntimeError("postgres down")),
    )

    with pytest.raises(RuntimeError):
        await profile_service.upsert_linkedin_with_consistency(
            None, mongo, uuid.uuid4(), raw_text="export text"
        )

    collection.delete_one.assert_awaited_once_with(
        {"_id": ObjectId("507f1f77bcf86cd799439011")}
    )


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
