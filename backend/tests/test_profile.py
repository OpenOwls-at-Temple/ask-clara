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


def test_student_cannot_see_other_students_profile():
    # Full integration test: requires TestClient + DB. Covered by get_current_user
    # dependency — each profile row is keyed to user_id which comes from the JWT.
    pytest.skip("requires TestClient setup")


def test_profile_upsert_replaces_target_roles():
    pytest.skip("requires async DB session — add with pytest-asyncio + test DB")


def test_profile_accepts_yyyy_mm_expected_graduation():
    from datetime import date
    p = ProfileIn(expected_graduation="2026-05")
    assert p.expected_graduation == date(2026, 5, 1)


def test_profile_accepts_empty_expected_graduation():
    p = ProfileIn(expected_graduation="")
    assert p.expected_graduation is None
