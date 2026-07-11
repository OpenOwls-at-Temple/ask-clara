import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

_ACCESS_EXPIRE_MINUTES = 15
_REFRESH_EXPIRE_DAYS = 7

bearer = HTTPBearer()


def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": exp}, settings.jwt_secret, algorithm="HS256"
    )


def create_refresh_token(user_id: str, token_version: int = 0) -> str:
    """Mint a refresh token carrying the user's current token_version ("tv").
    Bumping users.token_version on logout revokes every token minted before it."""
    exp = datetime.now(timezone.utc) + timedelta(days=_REFRESH_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "tv": token_version, "exp": exp},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> str:
    """Return the user_id (sub) from a valid access token, or raise 401."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return user_id


def decode_refresh_token(token: str) -> tuple[str, int]:
    """Return (user_id, token_version) from a valid refresh token, or raise 401.
    Tokens minted before versioning existed carry no "tv" claim and decode as 0,
    matching the column's server default — so they stay valid until first logout."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token"
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return user_id, int(payload.get("tv", 0))


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency — validates the Bearer access token and returns the User row."""
    user_id = decode_access_token(credentials.credentials)
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user
