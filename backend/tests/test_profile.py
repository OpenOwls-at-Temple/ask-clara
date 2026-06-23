import pytest


def test_student_cannot_see_other_students_profile():
    # TODO: create two users; assert GET /api/profile for user A does not return user B's data
    pytest.skip("not implemented")


def test_profile_upsert_replaces_target_roles():
    # TODO: create profile with 3 roles; upsert with different 3 roles; verify old roles gone
    pytest.skip("not implemented")


def test_ranked_roles_must_have_unique_ranks_1_to_3():
    # TODO: attempt to save two roles with the same rank; expect validation error
    pytest.skip("not implemented")
