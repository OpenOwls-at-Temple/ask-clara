import io
import uuid
from datetime import datetime

import pytest
from pypdf import PdfReader


SECTIONS = [
    {"heading": "Summary", "content": "Python developer with ML experience."},
    {
        "heading": "Experience",
        "content": (
            "- Built REST APIs in FastAPI\n"
            "- Reduced pipeline runtime by 40%\n"
            "- Led a 3-person team project"
        ),
    },
    {"heading": "Skills", "content": "Python, C# & F#, [brackets] {braces} $10k"},
]


def _pages(pdf_bytes: bytes) -> int:
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)


def _text(pdf_bytes: bytes) -> str:
    # New Computer Modern kerning makes pypdf insert stray spaces — strip
    # all whitespace so assertions are about content, not extraction quirks.
    text = "".join(
        page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf_bytes)).pages
    )
    return "".join(text.split())


def test_render_resume_pdf_produces_one_page_pdf():
    from app.services.resume_pdf import render_resume_pdf

    pdf = render_resume_pdf("Jane Student", SECTIONS)
    assert pdf.startswith(b"%PDF")
    assert _pages(pdf) == 1
    content = _text(pdf)
    assert "JaneStudent" in content
    assert "BuiltRESTAPIsinFastAPI" in content


def test_render_resume_pdf_escapes_typst_special_characters():
    from app.services.resume_pdf import render_resume_pdf

    # #, $, [, ], {, }, *, _ etc. must render literally, not error or vanish.
    pdf = render_resume_pdf("Jane Student", SECTIONS)
    content = _text(pdf)
    assert "C#&F#" in content
    assert "[brackets]" in content
    assert "{braces}" in content
    assert "$10k" in content


def test_render_resume_pdf_prefers_edited_text():
    from app.services.resume_pdf import render_resume_pdf

    pdf = render_resume_pdf(
        "Jane Student",
        SECTIONS,
        edited_text="MY EDITED RESUME\n- custom bullet",
    )
    content = _text(pdf)
    assert "MYEDITEDRESUME" in content
    assert "custombullet" in content
    # Section content is replaced by the edit
    assert "BuiltRESTAPIs" not in content


def test_render_resume_pdf_shrinks_to_fit_one_page():
    from app.services.resume_pdf import render_resume_pdf

    # Realistic upper bound: 6 sections near the ~120-word prompt cap.
    dense_sections = [
        {
            "heading": f"Section {i}",
            "content": "\n".join(
                f"- accomplished outcome {j} as measured by {j * 7}% by doing a "
                "specific action with Python and PostgreSQL"
                for j in range(6)
            ),
        }
        for i in range(6)
    ]
    pdf = render_resume_pdf("Jane Student", dense_sections)
    assert _pages(pdf) == 1


def test_render_resume_png_produces_an_image():
    from app.services.resume_pdf import render_resume_png

    png = render_resume_png("Jane Student", SECTIONS)
    assert png.startswith(b"\x89PNG")


def test_resume_pdf_never_includes_the_job_position():
    """The header carries the student's name only — a resume shouldn't be
    labeled with the posting/role it targets."""
    from app.services.resume_pdf import render_resume_pdf

    pdf = render_resume_pdf("Jane Student", SECTIONS)
    content = _text(pdf)
    assert "JaneStudent" in content
    assert "SoftwareEngineer" not in content
    assert "Engineer" not in content


# ---------------------------------------------------------------------------
# Download routes (real local Postgres, mocked Mongo)
# ---------------------------------------------------------------------------

VALID_OBJECT_ID = "64a2b3c4d5e6f7890a1b2c3d"


async def _seed_user(db_session, name="PDF Tester"):
    from app.models.user import User, UserRole

    user_id = uuid.uuid4()
    db_session.add(
        User(
            id=user_id,
            temple_email=f"{user_id.hex[:8]}@temple.edu",
            display_name=name,
            role=UserRole.student,
            created_at=datetime.utcnow(),
        )
    )
    await db_session.commit()
    return user_id


def _auth(user_id):
    from app.auth import create_access_token

    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def _mock_mongo(collection_doc):
    from unittest.mock import AsyncMock, MagicMock

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=collection_doc)
    mongo = MagicMock()
    mongo.__getitem__ = MagicMock(return_value=collection)
    return mongo


@pytest.mark.asyncio
async def test_download_resume_pdf_is_default_format(client, db_session):
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "target_title": "Software Engineer",
        "sections": SECTIONS,
        "edited_text": None,
    }
    with patch("app.routes.documents.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/resumes/{VALID_OBJECT_ID}/download", headers=_auth(user_id)
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        "clara-resume-software-engineer.pdf" in response.headers["content-disposition"]
    )
    assert response.content.startswith(b"%PDF")
    assert _pages(response.content) == 1


@pytest.mark.asyncio
async def test_download_resume_docx_still_available(client, db_session):
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "target_title": "Software Engineer",
        "sections": SECTIONS,
        "edited_text": None,
    }
    with patch("app.routes.documents.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/resumes/{VALID_OBJECT_ID}/download?format=docx",
            headers=_auth(user_id),
        )

    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_download_resume_png_preview_is_inline_image(client, db_session):
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "target_title": "Software Engineer",
        "sections": SECTIONS,
        "edited_text": None,
    }
    with patch("app.routes.documents.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/resumes/{VALID_OBJECT_ID}/download?format=png",
            headers=_auth(user_id),
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"] == "inline"
    assert response.content.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_download_materials_resume_png_preview(client, db_session):
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "posting": {"title": "SWE Intern", "employer": "Acme"},
        "resume_sections": SECTIONS,
    }
    with patch("app.routes.materials.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/materials/{VALID_OBJECT_ID}/resume/download?format=png",
            headers=_auth(user_id),
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_download_resume_rejects_unknown_format(client, db_session):
    user_id = await _seed_user(db_session)
    response = await client.get(
        f"/api/resumes/{VALID_OBJECT_ID}/download?format=html", headers=_auth(user_id)
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_download_resume_pdf_returns_503_when_typst_fails(client, db_session):
    """The route degrades gracefully — the UI falls back to DOCX/copy-text."""
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "target_title": "Engineer",
        "sections": SECTIONS,
        "edited_text": None,
    }
    with (
        patch("app.routes.documents.get_mongo_db", return_value=_mock_mongo(doc)),
        patch(
            "app.routes.documents.render_resume_pdf",
            side_effect=RuntimeError("typst exploded"),
        ),
    ):
        response = await client.get(
            f"/api/resumes/{VALID_OBJECT_ID}/download", headers=_auth(user_id)
        )
    assert response.status_code == 503
    assert "copy" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_materials_resume_pdf(client, db_session):
    from unittest.mock import patch

    user_id = await _seed_user(db_session)
    doc = {
        "user_id": str(user_id),
        "posting": {"title": "SWE Intern", "employer": "Acme"},
        "resume_sections": SECTIONS,
    }
    with patch("app.routes.materials.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/materials/{VALID_OBJECT_ID}/resume/download", headers=_auth(user_id)
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "clara-resume-swe-intern.pdf" in response.headers["content-disposition"]
    assert _pages(response.content) == 1


@pytest.mark.asyncio
async def test_student_cannot_download_another_students_resume_pdf(client, db_session):
    from unittest.mock import patch

    owner_id = await _seed_user(db_session, name="Owner")
    intruder_id = await _seed_user(db_session, name="Intruder")
    doc = {
        "user_id": str(owner_id),
        "target_title": "Engineer",
        "sections": SECTIONS,
        "edited_text": None,
    }
    with patch("app.routes.documents.get_mongo_db", return_value=_mock_mongo(doc)):
        response = await client.get(
            f"/api/resumes/{VALID_OBJECT_ID}/download", headers=_auth(intruder_id)
        )
    assert response.status_code == 404
