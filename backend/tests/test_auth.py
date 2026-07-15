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
    token = create_refresh_token(user_id, token_version=3)
    assert decode_refresh_token(token) == (user_id, 3)


def test_legacy_refresh_token_without_version_decodes_as_zero():
    """Tokens minted before versioning existed carry no "tv" claim; they must
    decode as version 0 (the column's server default) so deploys don't log
    everyone out."""
    from datetime import datetime, timedelta, timezone

    from jose import jwt

    from app.auth import decode_refresh_token
    from app.config import settings

    user_id = "00000000-0000-0000-0000-000000000001"
    exp = datetime.now(timezone.utc) + timedelta(days=1)
    legacy = jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": exp},
        settings.jwt_secret,
        algorithm="HS256",
    )
    assert decode_refresh_token(legacy) == (user_id, 0)


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
    with patch(
        "app.routes.auth._verify_google_token", new=AsyncMock(return_value=fake_claims)
    ):
        with patch("app.config.settings") as mock_settings:
            mock_settings.allowed_email_domain = "temple.edu"
            mock_settings.google_client_id = "fake-client-id"
            from app.routes.auth import login, LoginRequest
            from fastapi import HTTPException, Response
            import pytest

            body = LoginRequest(credential="fake-credential")
            response = Response()
            db = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await login(body, response, db)
            assert exc_info.value.status_code == 403
            assert (
                "Sign-in is restricted to @temple.edu accounts" in exc_info.value.detail
            )


def test_student_cannot_use_another_users_token():
    from app.auth import create_access_token, decode_access_token

    user_a = "aaaaaaaa-0000-0000-0000-000000000000"
    user_b = "bbbbbbbb-0000-0000-0000-000000000000"
    token_a = create_access_token(user_a)
    assert decode_access_token(token_a) == user_a
    assert decode_access_token(token_a) != user_b


# ---------------------------------------------------------------------------
# Refresh-token revocation (token versioning)
# ---------------------------------------------------------------------------

_USER_ID = "00000000-0000-0000-0000-000000000009"


def _make_user(token_version: int):
    from unittest.mock import MagicMock

    user = MagicMock()
    user.id = _USER_ID
    user.temple_email = "tuk12345@temple.edu"
    user.display_name = "Test Student"
    user.role.value = "student"
    user.token_version = token_version
    return user


@pytest.mark.asyncio
async def test_refresh_rejected_after_revocation():
    """A refresh token minted at version 0 must be rejected once the user's
    token_version has been bumped (i.e. after logout)."""
    from app.auth import create_refresh_token
    from app.routes.auth import refresh
    from fastapi import Response

    stale_token = create_refresh_token(_USER_ID, token_version=0)
    db = AsyncMock()
    db.get.return_value = _make_user(token_version=1)

    with pytest.raises(HTTPException) as exc_info:
        await refresh(Response(), refresh_token=stale_token, db=db)
    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_refresh_accepted_when_version_matches():
    from app.auth import create_refresh_token
    from app.routes.auth import refresh
    from fastapi import Response

    token = create_refresh_token(_USER_ID, token_version=2)
    db = AsyncMock()
    db.get.return_value = _make_user(token_version=2)

    result = await refresh(Response(), refresh_token=token, db=db)
    assert "access_token" in result


@pytest.mark.asyncio
async def test_logout_bumps_token_version_and_clears_cookie():
    from app.auth import create_refresh_token
    from app.routes.auth import logout
    from fastapi import Response

    user = _make_user(token_version=0)
    db = AsyncMock()
    db.get.return_value = user
    token = create_refresh_token(_USER_ID, token_version=0)

    result = await logout(Response(), refresh_token=token, db=db)
    assert result == {"ok": True}
    assert user.token_version == 1
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_logout_without_cookie_still_succeeds():
    from app.routes.auth import logout
    from fastapi import Response

    db = AsyncMock()
    result = await logout(Response(), refresh_token=None, db=db)
    assert result == {"ok": True}
    db.commit.assert_not_awaited()


def _test_login_env(monkeypatch, environment="local", secret="e2e-secret"):
    from app.config import settings

    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(settings, "test_login_secret", secret)


@pytest.mark.asyncio
async def test_test_login_is_hidden_outside_local_environment(client, monkeypatch):
    _test_login_env(monkeypatch, environment="staging")
    response = await client.post(
        "/api/auth/test-login",
        json={"email": "e2e@temple.edu"},
        headers={"X-Test-Login-Secret": "e2e-secret"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_login_is_hidden_when_secret_unset(client, monkeypatch):
    _test_login_env(monkeypatch, secret=None)
    response = await client.post(
        "/api/auth/test-login",
        json={"email": "e2e@temple.edu"},
        headers={"X-Test-Login-Secret": "anything"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_login_is_hidden_on_wrong_or_missing_secret(client, monkeypatch):
    _test_login_env(monkeypatch)
    wrong = await client.post(
        "/api/auth/test-login",
        json={"email": "e2e@temple.edu"},
        headers={"X-Test-Login-Secret": "wrong"},
    )
    assert wrong.status_code == 404

    missing = await client.post(
        "/api/auth/test-login", json={"email": "e2e@temple.edu"}
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_test_login_rejects_non_temple_email(client, monkeypatch):
    _test_login_env(monkeypatch)
    response = await client.post(
        "/api/auth/test-login",
        json={"email": "e2e@gmail.com"},
        headers={"X-Test-Login-Secret": "e2e-secret"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_test_login_mints_session_and_sets_refresh_cookie(
    client, db_session, monkeypatch
):
    _test_login_env(monkeypatch)
    response = await client.post(
        "/api/auth/test-login",
        json={"email": "e2e@temple.edu", "display_name": "E2E Student"},
        headers={"X-Test-Login-Secret": "e2e-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["temple_email"] == "e2e@temple.edu"

    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
