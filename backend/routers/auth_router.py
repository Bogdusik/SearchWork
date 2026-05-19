import os
import secrets
from typing import Annotated

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    refresh_token_expiry,
    verify_password,
    _decode,
    _SECRET,
    _ALGORITHM,
)
from database import get_db
from models import RefreshToken, User
from schemas import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

_SECURE_COOKIE = os.getenv("ENV", "development") != "development"
_SAMESITE = "none" if _SECURE_COOKIE else "lax"
_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
_GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
_GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite=_SAMESITE,
        max_age=7 * 24 * 60 * 60,
        path="/auth/refresh",
    )


async def _store_refresh_token(db: AsyncSession, user_id: int, token: str) -> None:
    db.add(RefreshToken(token=token, user_id=user_id, expires_at=refresh_token_expiry()))
    await db.commit()


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def register(request: Request, body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    refresh = create_refresh_token(user.id)
    await _store_refresh_token(db, user.id, refresh)
    _set_refresh_cookie(response, refresh)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenOut)
@limiter.limit("20/minute")
async def login(request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    refresh = create_refresh_token(user.id)
    await _store_refresh_token(db, user.id, refresh)
    _set_refresh_cookie(response, refresh)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token invalid or already used")

    user_id = _decode(refresh_token)

    await db.execute(delete(RefreshToken).where(RefreshToken.token == refresh_token))
    await db.commit()

    new_refresh = create_refresh_token(user_id)
    await _store_refresh_token(db, user_id, new_refresh)
    _set_refresh_cookie(response, new_refresh)
    return TokenOut(access_token=create_access_token(user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        await db.execute(delete(RefreshToken).where(RefreshToken.token == refresh_token))
        await db.commit()
    response.delete_cookie("refresh_token", path="/auth/refresh")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/google/url")
async def google_url():
    if not _GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google OAuth not configured")
    state = jwt.encode({"nonce": secrets.token_hex(16)}, _SECRET, algorithm=_ALGORITHM)
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={_GOOGLE_CLIENT_ID}"
        f"&redirect_uri={_GOOGLE_REDIRECT_URI}"
        f"&scope=openid+email"
        f"&state={state}"
        f"&access_type=offline"
    )
    return {"url": url}


@router.get("/google/callback")
async def google_callback(code: str, state: str, response: Response, db: AsyncSession = Depends(get_db)):
    if not _GOOGLE_CLIENT_ID or not _GOOGLE_CLIENT_SECRET:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google OAuth not configured")

    try:
        jwt.decode(state, _SECRET, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")

    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
                "redirect_uri": _GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google token exchange failed")
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Failed to fetch Google user info")
        userinfo = userinfo_resp.json()

    google_id: str = userinfo["sub"]
    email: str = userinfo["email"]

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        existing = await db.execute(select(User).where(User.email == email))
        user = existing.scalar_one_or_none()
        if user:
            user.google_id = google_id
        else:
            user = User(email=email, google_id=google_id)
            db.add(user)
        await db.commit()
        await db.refresh(user)

    refresh = create_refresh_token(user.id)
    await _store_refresh_token(db, user.id, refresh)

    redirect = RedirectResponse(url=f"{_FRONTEND_URL}/auth/callback?access_token={create_access_token(user.id)}")
    redirect.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite=_SAMESITE,
        max_age=7 * 24 * 60 * 60,
        path="/auth/refresh",
    )
    return redirect
