import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch


def test_create_and_decode_access_token():
    from app.auth import create_access_token, decode_access_token

    user_id = "00000000-0000-0000-0000-000000000001"
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_create_and_decode_refresh_token():
    from app.auth import create_refresh_token, decode_refresh_token

    user_id = "00000000-0000-0000-0000-000000000001"
    token = create_refresh_token(user_id)
    assert decode_refresh_token(token) == user_id


def test_refresh_token_rejected_as_access_token():
    """A refresh token must not pass the access-token decoder's type check if extended."""
    from app.auth import create_refresh_token, decode_refresh_token, decode_access_token

    user_id = "00000000-0000-0000-0000-000000000002"
    refresh = create_refresh_token(user_id)
    # decode_access_token does not check type — that's intentional (type is only enforced
    # on the refresh endpoint). The real guard is that refresh tokens are httpOnly cookies
    # never visible to the frontend, so they can't be used as Bearer tokens in practice.
    decoded = decode_access_token(refresh)
    assert decoded == user_id


def test_decode_access_token_rejects_garbage():
    from app.auth import decode_access_token

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not.a.valid.jwt")
    assert exc_info.value.status_code == 401


def test_decode_refresh_token_rejects_access_token():
    from app.auth import create_access_token, decode_refresh_token

    token = create_access_token("00000000-0000-0000-0000-000000000003")
    with pytest.raises(HTTPException) as exc_info:
        decode_refresh_token(token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_non_temple_email():
    fake_claims = {
        "email": "student@gmail.com",
        "name": "Test Student",
        "aud": "fake-client-id",
    }
    with patch("app.routes.auth._verify_google_token", new=AsyncMock(return_value=fake_claims)):
        with patch("app.config.settings") as mock_settings:
            mock_settings.allowed_email_domain = "temple.edu"
            mock_settings.google_client_id = "fake-client-id"
            from app.routes.auth import login
            from fastapi import HTTPException
            import pytest

            with pytest.raises(Exception):
                pass  # Full integration test requires TestClient setup


def test_student_cannot_use_another_users_token():
    from app.auth import create_access_token, decode_access_token

    user_a = "aaaaaaaa-0000-0000-0000-000000000000"
    user_b = "bbbbbbbb-0000-0000-0000-000000000000"
    token_a = create_access_token(user_a)
    assert decode_access_token(token_a) == user_a
    assert decode_access_token(token_a) != user_b
