import asyncio
import logging
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from unittest.mock import AsyncMock, patch

from models import AlertSettings, User
from services import alert_scheduler
from tests.conftest import TestSession, test_engine, TEST_USER_ID

NOW = datetime(2026, 11, 27, 12, 0, 0)
INTERVAL = timedelta(hours=6)


async def add_settings(user_id: int, *, enabled: bool = True, last_scan_at: datetime | None) -> None:
    async with TestSession() as session:
        session.add(AlertSettings(user_id=user_id, enabled=enabled, query="junior developer", locations=[],
                                  min_score=70, ntfy_topic=f"topic-for-user-{user_id}", last_scan_at=last_scan_at))
        await session.commit()


async def add_user(email: str) -> int:
    async with TestSession() as session:
        user = User(email=email, hashed_password="hashed")
        session.add(user)
        await session.commit()
        return user.id


async def last_scans() -> dict[int, datetime | None]:
    async with TestSession() as session:
        rows = (await session.execute(select(AlertSettings))).scalars().all()
        return {r.user_id: r.last_scan_at for r in rows}


async def tick(now: datetime = NOW, scan: AsyncMock | None = None) -> tuple[alert_scheduler.TickResult, AsyncMock]:
    scan = scan or AsyncMock()
    with patch("services.alert_scheduler.alert_service.scan_user", scan):
        result = await alert_scheduler.run_due_scans(TestSession, test_engine, now_fn=lambda: now)
    return result, scan


def scanned_user_ids(scan: AsyncMock) -> list[int]:
    return [c.args[1].user_id for c in scan.await_args_list]


@pytest.fixture(autouse=True)
def fixed_interval(monkeypatch):
    monkeypatch.setenv("ALERT_SCAN_INTERVAL_HOURS", "6")


@pytest.mark.asyncio
async def test_tick_scans_due_and_never_scanned_users_only():
    recent = await add_user("recent@example.com")
    disabled = await add_user("disabled@example.com")
    stale = await add_user("stale@example.com")
    await add_settings(TEST_USER_ID, last_scan_at=None)
    await add_settings(recent, last_scan_at=NOW - timedelta(hours=1))
    await add_settings(disabled, enabled=False, last_scan_at=None)
    await add_settings(stale, last_scan_at=NOW - INTERVAL)

    _, scan = await tick()

    assert sorted(scanned_user_ids(scan)) == sorted([TEST_USER_ID, stale])
    scans = await last_scans()
    assert scans[TEST_USER_ID] == NOW
    assert scans[stale] == NOW
    assert scans[recent] == NOW - timedelta(hours=1)
    assert scans[disabled] is None


@pytest.mark.asyncio
async def test_missed_intervals_are_not_replayed_after_sleep():
    await add_settings(TEST_USER_ID, last_scan_at=NOW - 3 * INTERVAL)

    _, first = await tick()
    _, second = await tick(now=NOW + timedelta(minutes=15))

    assert first.await_count == 1
    second.assert_not_awaited()


@pytest.mark.asyncio
async def test_tick_skips_when_another_tick_holds_the_lock(caplog):
    await add_settings(TEST_USER_ID, last_scan_at=None)

    with caplog.at_level(logging.INFO):
        async with alert_scheduler._single_flight(test_engine) as acquired:
            assert acquired is True
            result, scan = await tick()

    assert result.skipped is True
    scan.assert_not_awaited()
    assert "skipped" in caplog.text
    assert (await last_scans())[TEST_USER_ID] is None


@pytest.mark.asyncio
async def test_lock_is_released_after_a_failing_tick():
    await add_settings(TEST_USER_ID, last_scan_at=None)

    with patch("services.alert_scheduler._due_user_ids", AsyncMock(side_effect=RuntimeError("db hiccup"))):
        with pytest.raises(RuntimeError):
            await alert_scheduler.run_due_scans(TestSession, test_engine, now_fn=lambda: NOW)

    result, scan = await tick()
    assert result.skipped is False
    assert scan.await_count == 1


@pytest.mark.asyncio
async def test_one_users_failing_scan_does_not_stop_the_others(caplog):
    other = await add_user("other@example.com")
    await add_settings(TEST_USER_ID, last_scan_at=None)
    await add_settings(other, last_scan_at=None)

    async def scan(db, settings):
        if settings.user_id == TEST_USER_ID:
            raise RuntimeError("job source exploded")

    with caplog.at_level(logging.INFO):
        result, mock = await tick(scan=AsyncMock(side_effect=scan))

    assert sorted(scanned_user_ids(mock)) == sorted([TEST_USER_ID, other])
    assert result.failed == 1
    scans = await last_scans()
    assert scans[TEST_USER_ID] == NOW
    assert scans[other] == NOW
    assert "topic-for-user" not in caplog.text


@pytest.mark.asyncio
async def test_loop_runs_a_tick_immediately_and_survives_tick_errors():
    run = AsyncMock(side_effect=[RuntimeError("boom"), alert_scheduler.TickResult()])
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        if len(sleeps) == 2:
            raise asyncio.CancelledError

    with patch("services.alert_scheduler.run_due_scans", run), \
         patch("services.alert_scheduler.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await alert_scheduler.alert_loop()

    assert run.await_count == 2
    assert sleeps == [alert_scheduler.TICK_SECONDS, alert_scheduler.TICK_SECONDS]


def test_scheduler_is_enabled_by_default_and_can_be_switched_off(monkeypatch):
    monkeypatch.delenv("ALERT_SCHEDULER_ENABLED", raising=False)
    assert alert_scheduler.scheduler_enabled() is True

    monkeypatch.setenv("ALERT_SCHEDULER_ENABLED", "false")
    assert alert_scheduler.scheduler_enabled() is False


@pytest.mark.parametrize("raw", ["", "   ", "not-a-number", "0", "-2"])
def test_blank_or_invalid_scan_interval_falls_back_to_six_hours(monkeypatch, raw):
    monkeypatch.setenv("ALERT_SCAN_INTERVAL_HOURS", raw)

    assert alert_scheduler.scan_interval() == timedelta(hours=6)


def test_decimal_scan_interval_is_accepted(monkeypatch):
    monkeypatch.setenv("ALERT_SCAN_INTERVAL_HOURS", "0.05")

    assert alert_scheduler.scan_interval() == timedelta(minutes=3)


def test_blank_scheduler_flag_keeps_the_scheduler_on(monkeypatch):
    monkeypatch.setenv("ALERT_SCHEDULER_ENABLED", "")

    assert alert_scheduler.scheduler_enabled() is True
