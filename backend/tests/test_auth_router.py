from datetime import datetime, timezone

import bcrypt
import pytest

import auth
from models import User
from tests.conftest import TestSession

PASSWORD = "s3cret-pw"
FROZEN_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def frozen_clock(monkeypatch):
    monkeypatch.setattr(auth, "_utcnow", lambda: FROZEN_NOW)


async def register(client, email, password=PASSWORD):
    return await client.post("/auth/register", json={"email": email, "password": password})


async def login(client, email, password=PASSWORD):
    return await client.post("/auth/login", json={"email": email, "password": password})


@pytest.mark.asyncio
async def test_register_returns_201_with_token_and_refresh_cookie(client):
    resp = await register(client, "new@example.com", "abcdefgh")
    assert resp.status_code == 201
    assert resp.json()["access_token"]
    assert "refresh_token=" in resp.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_register_accepts_password_over_72_bytes(client):
    resp = await register(client, "long@example.com", "a" * 100)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_login_after_register(client):
    await register(client, "login@example.com")
    resp = await login(client, "login@example.com")
    assert resp.status_code == 200
    assert resp.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await register(client, "wrong@example.com")
    resp = await login(client, "wrong@example.com", "not-the-password")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client):
    resp = await login(client, "nobody@example.com")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


async def add_user_with_legacy_hash(email):
    legacy_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(12)).decode()
    assert legacy_hash.startswith("$2b$12$")
    async with TestSession() as session:
        session.add(User(email=email, hashed_password=legacy_hash))
        await session.commit()


@pytest.mark.asyncio
async def test_hash_created_before_change_still_verifies(client):
    await add_user_with_legacy_hash("legacy@example.com")
    resp = await login(client, "legacy@example.com")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_hash_created_before_change_rejects_wrong_password(client):
    await add_user_with_legacy_hash("legacy-bad@example.com")
    resp = await login(client, "legacy-bad@example.com", "not-the-password")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_then_login_in_same_second_issue_distinct_refresh_tokens(client, frozen_clock):
    registered = await register(client, "same-second@example.com")
    logged_in = await login(client, "same-second@example.com")
    assert registered.status_code == 201
    assert logged_in.status_code == 200
    assert registered.cookies["refresh_token"] != logged_in.cookies["refresh_token"]


@pytest.mark.asyncio
async def test_two_logins_in_same_second_issue_distinct_refresh_tokens(client, frozen_clock):
    async with TestSession() as session:
        session.add(User(email="twice@example.com", hashed_password=auth.hash_password(PASSWORD)))
        await session.commit()

    first = await login(client, "twice@example.com")
    second = await login(client, "twice@example.com")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.cookies["refresh_token"] != second.cookies["refresh_token"]


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await register(client, "dup@example.com")
    resp = await register(client, "dup@example.com")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client):
    resp = await register(client, "short@example.com", "abcdefg")
    assert resp.status_code == 422
