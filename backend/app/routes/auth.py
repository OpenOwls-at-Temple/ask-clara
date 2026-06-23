from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import CurrentUser, TokenResponse

router = APIRouter()


@router.get("/me", response_model=CurrentUser)
async def me():
    # TODO: extract user from JWT; return CurrentUser
    raise NotImplementedError


@router.post("/login", response_model=TokenResponse)
async def login(response: Response, db: AsyncSession = Depends(get_db)):
    # TODO: validate Google SSO code, enforce @temple.edu domain,
    #       upsert User row, issue JWT access token + httpOnly refresh cookie
    raise NotImplementedError


@router.post("/logout")
async def logout(response: Response):
    # TODO: invalidate refresh token cookie
    response.delete_cookie("refresh_token")
    return {"ok": True}
