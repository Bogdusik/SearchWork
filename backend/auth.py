import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User

_SECRET = os.getenv("SECRET_KEY", "")
_ALGORITHM = "HS256"
_ACCESS_EXPIRES = timedelta(minutes=30)
_REFRESH_EXPIRES = timedelta(days=7)

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer()


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": _utcnow() + _ACCESS_EXPIRES}
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": _utcnow() + _REFRESH_EXPIRES}
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def refresh_token_expiry() -> datetime:
    return (_utcnow() + _REFRESH_EXPIRES).replace(tzinfo=None)


def _decode(token: str) -> int:
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = _decode(credentials.credentials)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user
