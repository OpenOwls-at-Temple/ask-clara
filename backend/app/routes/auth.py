import secrets
import uuid

import httpx
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
)
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import CurrentUser
from app.services.auth_service import upsert_user

router = APIRouter()

_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 7 * 24 * 3600
_REFRESH_PATH = "/api/auth"


class LoginRequest(BaseModel):
    credential: str  # Google ID token obtained by the frontend via GIS


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        _REFRESH_COOKIE,
        token,
        httponly=True,
        secure=settings.environment != "local",
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        path=_REFRESH_PATH,
    )


def _user_out(user: User) -> CurrentUser:
    return CurrentUser(
        id=str(user.id),
        temple_email=user.temple_email,
        display_name=user.display_name,
        role=user.role.value,
    )


async def _verify_google_token(credential: str) -> dict:
    """Verify a Google ID token via Google's tokeninfo endpoint."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
        )
    if r.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        )
    claims = r.json()
    if claims.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token audience mismatch",
        )
    return claims


@router.get("/me", response_model=CurrentUser)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    claims = await _verify_google_token(body.credential)

    email: str = claims.get("email", "")
    if not email.endswith(f"@{settings.allowed_email_domain}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sign-in is restricted to @{settings.allowed_email_domain} accounts",
        )

    user = await upsert_user(
        db,
        email=email,
        display_name=claims.get("name", email),
    )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id), user.token_version)
    _set_refresh_cookie(response, refresh_token)

    return {"access_token": access_token, "user": _user_out(user)}


class TestLoginRequest(BaseModel):
    email: str
    display_name: str = "E2E Test Student"


@router.post("/test-login")
async def test_login(
    body: TestLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    x_test_login_secret: str | None = Header(default=None),
):
    """E2E-only: mint a session for a synthetic local user without Google.

    Triple-gated — 404s (indistinguishable from a nonexistent route) unless
    the environment is local, TEST_LOGIN_SECRET is configured, and the caller
    presents it. Authorization checks downstream are fully enforced; this
    endpoint only replaces the Google credential exchange.
    """
    if (
        settings.environment != "local"
        or not settings.test_login_secret
        or not x_test_login_secret
        or not secrets.compare_digest(x_test_login_secret, settings.test_login_secret)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    if not body.email.endswith(f"@{settings.allowed_email_domain}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sign-in is restricted to @{settings.allowed_email_domain} accounts",
        )

    user = await upsert_user(db, email=body.email, display_name=body.display_name)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id), user.token_version)
    _set_refresh_cookie(response, refresh_token)

    return {"access_token": access_token, "user": _user_out(user)}


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
        )

    user_id, token_version = decode_refresh_token(refresh_token)
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    if token_version != user.token_version:
        # Minted before the user's last logout — revoked.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id), user.token_version)
    _set_refresh_cookie(response, new_refresh)

    return {"access_token": new_access, "user": _user_out(user)}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    # Server-side revocation: bump token_version so every outstanding refresh
    # token for this user (this browser's and any stolen copy's) stops working.
    # Authenticated by the refresh cookie itself — the access token may already
    # have expired when the user clicks "Sign out".
    if refresh_token:
        try:
            user_id, _ = decode_refresh_token(refresh_token)
            user = await db.get(User, uuid.UUID(user_id))
            if user is not None:
                user.token_version += 1
                await db.commit()
        except HTTPException:
            pass  # invalid/expired cookie — nothing to revoke
    response.delete_cookie(_REFRESH_COOKIE, path=_REFRESH_PATH)
    return {"ok": True}
