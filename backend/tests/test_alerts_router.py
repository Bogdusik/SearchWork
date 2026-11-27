import json
import logging
from datetime import datetime

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from unittest.mock import AsyncMock, patch

from auth import get_current_user
from main import app
from models import AlertSettings, User
from tests.conftest import TestSession, TEST_USER_ID, override_get_current_user

TOPIC = "sw-test-topic-9f3k2"

VALID_SETTINGS = {
    "enabled": True,
    "query": "junior python developer",
    "locations": ["Glasgow", "Edinburgh"],
    "min_score": 70,
    "ntfy_topic": TOPIC,
}


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limits():
    from routers import alerts
    alerts.limiter.reset()
    yield


async def _settings_rows() -> list[AlertSettings]:
    async with TestSession() as session:
        return list((await session.execute(select(AlertSettings))).scalars().all())


@pytest.mark.asyncio
async def test_get_alerts_without_settings_returns_null(client):
    resp = await client.get("/alerts")

    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_put_alerts_stores_and_returns_settings(client):
    resp = await client.put("/alerts", json=VALID_SETTINGS)

    assert resp.status_code == 200
    body = resp.json()
    for key, value in VALID_SETTINGS.items():
        assert body[key] == value
    assert body["last_scan_at"] is None

    fetched = await client.get("/alerts")
    assert fetched.json()["query"] == "junior python developer"


@pytest.mark.asyncio
async def test_second_put_updates_the_same_row(client):
    await client.put("/alerts", json=VALID_SETTINGS)
    resp = await client.put("/alerts", json={**VALID_SETTINGS, "min_score": 55, "enabled": False})

    assert resp.status_code == 200
    rows = await _settings_rows()
    assert len(rows) == 1
    assert rows[0].min_score == 55
    assert rows[0].enabled is False


@pytest.mark.asyncio
async def test_put_alerts_accepts_empty_locations(client):
    resp = await client.put("/alerts", json={**VALID_SETTINGS, "locations": []})

    assert resp.status_code == 200
    assert resp.json()["locations"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("override", [
    {"query": ""},
    {"query": "   "},
    {"query": "x" * 201},
    {"min_score": -1},
    {"min_score": 101},
    {"locations": [f"City{i}" for i in range(11)]},
    {"locations": ["x" * 101]},
    {"ntfy_topic": "short"},
    {"ntfy_topic": "has spaces in it"},
    {"ntfy_topic": "slash/in/topic"},
    {"ntfy_topic": "x" * 65},
])
async def test_put_alerts_rejects_invalid_input(client, override):
    resp = await client.put("/alerts", json={**VALID_SETTINGS, **override})

    assert resp.status_code == 422
    assert await _settings_rows() == []


@pytest.mark.asyncio
async def test_validation_error_does_not_echo_topic(client):
    bad_topic = "bad topic with secret-ish name"
    resp = await client.put("/alerts", json={**VALID_SETTINGS, "ntfy_topic": bad_topic})

    assert resp.status_code == 422
    assert bad_topic not in resp.text


ENDPOINTS = [("get", "/alerts"), ("put", "/alerts"), ("post", "/alerts/test")]


async def _call_without_override(client, method: str, path: str, headers: dict[str, str]):
    app.dependency_overrides.pop(get_current_user)
    try:
        kwargs = {"json": VALID_SETTINGS} if method == "put" else {}
        return await getattr(client, method)(path, headers=headers, **kwargs)
    finally:
        app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_alerts_endpoints_reject_invalid_token_with_401(client, method, path):
    resp = await _call_without_override(client, method, path, {"Authorization": "Bearer not-a-jwt"})

    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ENDPOINTS)
async def test_alerts_endpoints_reject_missing_token_like_other_routes(client, method, path):
    resp = await _call_without_override(client, method, path, {})

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_see_or_change_another_users_settings(client):
    async with TestSession() as session:
        other = User(email="other@example.com", hashed_password="hashed")
        session.add(other)
        await session.flush()
        session.add(AlertSettings(
            user_id=other.id, enabled=True, query="other query",
            locations=[], min_score=10, ntfy_topic="other-users-topic",
        ))
        await session.commit()

    assert (await client.get("/alerts")).json() is None

    await client.put("/alerts", json=VALID_SETTINGS)

    rows = {r.user_id: r for r in await _settings_rows()}
    assert rows[TEST_USER_ID].query == "junior python developer"
    other_row = next(r for uid, r in rows.items() if uid != TEST_USER_ID)
    assert other_row.query == "other query"
    assert other_row.ntfy_topic == "other-users-topic"


@pytest.mark.asyncio
async def test_send_test_push_without_settings_returns_404(client):
    with patch("routers.alerts.ntfy_service.send_push", new_callable=AsyncMock) as send:
        resp = await client.post("/alerts/test")

    assert resp.status_code == 404
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_test_push_sends_one_push_to_users_topic(client):
    await client.put("/alerts", json=VALID_SETTINGS)
    with patch("routers.alerts.ntfy_service.send_push", new_callable=AsyncMock) as send:
        resp = await client.post("/alerts/test")

    assert resp.status_code == 204
    send.assert_awaited_once()
    assert send.await_args.kwargs["topic"] == TOPIC
    assert send.await_args.kwargs["title"] == "SearchWork test"


@pytest.mark.asyncio
async def test_send_test_push_returns_502_when_ntfy_fails_without_leaking_topic(client, caplog):
    from services.ntfy_service import NtfyError

    await client.put("/alerts", json=VALID_SETTINGS)
    with caplog.at_level(logging.DEBUG), \
         patch("routers.alerts.ntfy_service.send_push", new_callable=AsyncMock, side_effect=NtfyError("ntfy returned 500")):
        resp = await client.post("/alerts/test")

    assert resp.status_code == 502
    assert TOPIC not in resp.text
    assert TOPIC not in caplog.text


@pytest.mark.asyncio
async def test_send_test_push_is_rate_limited_to_three_per_minute(client):
    await client.put("/alerts", json=VALID_SETTINGS)
    with patch("routers.alerts.ntfy_service.send_push", new_callable=AsyncMock):
        statuses = [(await client.post("/alerts/test")).status_code for _ in range(4)]

    assert statuses == [204, 204, 204, 429]


@pytest.mark.asyncio
async def test_llms_txt_documents_alert_endpoints(client):
    resp = await client.get("/llms.txt")

    assert "GET /alerts" in resp.text
    assert "PUT /alerts" in resp.text
    assert "POST /alerts/test" in resp.text


@pytest.mark.asyncio
async def test_send_push_publishes_json_with_topic_title_and_click(monkeypatch):
    from services import ntfy_service

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"id": "abc"})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(ntfy_service.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(ntfy_service, "NTFY_URL", "https://ntfy.example")

    await ntfy_service.send_push(topic=TOPIC, title="Développeur — £30k at Corp", message="Score 85",
                                 click_url="https://example.com/job/1")

    assert len(captured) == 1
    req = captured[0]
    assert str(req.url) == "https://ntfy.example"
    payload = json.loads(req.content)
    assert payload["topic"] == TOPIC
    assert payload["title"] == "Développeur — £30k at Corp"
    assert payload["message"] == "Score 85"
    assert payload["click"] == "https://example.com/job/1"


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [
    lambda request: httpx.Response(500, text="boom"),
    lambda request: (_ for _ in ()).throw(httpx.ConnectError("down")),
])
async def test_send_push_raises_ntfy_error_without_topic(monkeypatch, handler):
    from services import ntfy_service

    real_client = httpx.AsyncClient
    monkeypatch.setattr(ntfy_service.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))

    with pytest.raises(ntfy_service.NtfyError) as exc:
        await ntfy_service.send_push(topic=TOPIC, title="t", message="m")

    assert TOPIC not in str(exc.value)


async def _set_baseline_done() -> None:
    async with TestSession() as session:
        row = (await session.execute(select(AlertSettings))).scalar_one()
        row.baseline_at = datetime(2026, 11, 1)
        await session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", [{"query": "graduate data engineer"}, {"locations": ["Leeds"]}])
async def test_changing_query_or_cities_restarts_the_silent_baseline(client, change):
    await client.put("/alerts", json=VALID_SETTINGS)
    await _set_baseline_done()

    await client.put("/alerts", json={**VALID_SETTINGS, **change})

    assert (await _settings_rows())[0].baseline_at is None


@pytest.mark.asyncio
async def test_changing_only_score_topic_or_toggle_keeps_the_baseline(client):
    await client.put("/alerts", json=VALID_SETTINGS)
    await _set_baseline_done()

    await client.put("/alerts", json={**VALID_SETTINGS, "min_score": 50, "enabled": False,
                                      "ntfy_topic": "another-topic-123"})

    assert (await _settings_rows())[0].baseline_at is not None


@pytest.mark.asyncio
async def test_put_racing_with_a_first_insert_updates_instead_of_500(client, monkeypatch):
    from routers import alerts

    await client.put("/alerts", json=VALID_SETTINGS)
    real_get = alerts._get_settings
    calls = 0

    async def stale_first_lookup(db, user_id):
        nonlocal calls
        calls += 1
        return None if calls == 1 else await real_get(db, user_id)

    monkeypatch.setattr(alerts, "_get_settings", stale_first_lookup)

    resp = await client.put("/alerts", json={**VALID_SETTINGS, "min_score": 42})

    assert resp.status_code == 200
    assert resp.json()["min_score"] == 42
    rows = await _settings_rows()
    assert len(rows) == 1 and rows[0].min_score == 42


@pytest.mark.parametrize("raw,expected", [
    ("", "https://ntfy.sh"),
    ("   ", "https://ntfy.sh"),
    ("https://ntfy.example/", "https://ntfy.example"),
])
def test_ntfy_url_treats_blank_as_default(monkeypatch, raw, expected):
    from services import ntfy_service

    monkeypatch.setenv("NTFY_URL", raw)

    assert ntfy_service.resolve_ntfy_url() == expected
