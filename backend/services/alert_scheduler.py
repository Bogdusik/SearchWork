import asyncio
import logging
import os
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models import AlertSettings
from services import alert_service
from utils import _utcnow

logger = logging.getLogger(__name__)

TICK_SECONDS = 15 * 60
# Arbitrary fixed key for pg_try_advisory_xact_lock; any process using the same DB contends for it.
ADVISORY_LOCK_KEY = 0x53574A41

_in_process_lock = asyncio.Lock()


@dataclass
class TickResult:
    skipped: bool = False
    scanned: int = 0
    failed: int = 0


DEFAULT_SCAN_INTERVAL_HOURS = 6.0


def scheduler_enabled() -> bool:
    return (os.getenv("ALERT_SCHEDULER_ENABLED") or "").strip().lower() != "false"


def scan_interval() -> timedelta:
    raw = (os.getenv("ALERT_SCAN_INTERVAL_HOURS") or "").strip()
    try:
        hours = float(raw) if raw else DEFAULT_SCAN_INTERVAL_HOURS
    except ValueError:
        hours = 0.0
    if hours <= 0:
        logger.warning("ALERT_SCAN_INTERVAL_HOURS must be a positive number, using %s", DEFAULT_SCAN_INTERVAL_HOURS)
        hours = DEFAULT_SCAN_INTERVAL_HOURS
    return timedelta(hours=hours)


@asynccontextmanager
async def _single_flight(engine: AsyncEngine) -> AsyncIterator[bool]:
    if engine.dialect.name == "postgresql":
        # Transaction-scoped lock: released on commit/rollback or when the connection dies,
        # so a crashed tick or a pooled connection can never keep it held.
        async with engine.connect() as conn, conn.begin():
            acquired = (await conn.execute(select(func.pg_try_advisory_xact_lock(ADVISORY_LOCK_KEY)))).scalar()
            yield bool(acquired)
        return

    if _in_process_lock.locked():
        yield False
        return
    async with _in_process_lock:
        yield True


async def _due_user_ids(db: AsyncSession, cutoff: datetime) -> list[int]:
    rows = await db.execute(
        select(AlertSettings.user_id)
        .where(AlertSettings.enabled.is_(True))
        .where(or_(AlertSettings.last_scan_at.is_(None), AlertSettings.last_scan_at <= cutoff))
        .order_by(AlertSettings.user_id)
    )
    return list(rows.scalars().all())


async def _scan_one(session_factory: sessionmaker, user_id: int, now_fn: Callable[[], datetime]) -> bool:
    async with session_factory() as db:
        settings = (await db.execute(
            select(AlertSettings).where(AlertSettings.user_id == user_id)
        )).scalar_one_or_none()
        if settings is None or not settings.enabled:
            return True
        ok = True
        try:
            await alert_service.scan_user(db, settings)
        except Exception as exc:
            ok = False
            await db.rollback()
            logger.error("Alert scan failed for user %s: %s", user_id, type(exc).__name__)
        # Stamped even after a failure so a persistent error costs one attempt per interval, not one per tick.
        settings.last_scan_at = now_fn()
        await db.commit()
        return ok


async def run_due_scans(
    session_factory: sessionmaker,
    engine: AsyncEngine,
    now_fn: Callable[[], datetime] = _utcnow,
) -> TickResult:
    async with _single_flight(engine) as acquired:
        if not acquired:
            logger.info("Alert tick skipped: another tick is still running")
            return TickResult(skipped=True)

        async with session_factory() as db:
            user_ids = await _due_user_ids(db, now_fn() - scan_interval())

        result = TickResult()
        for user_id in user_ids:
            ok = await _scan_one(session_factory, user_id, now_fn)
            result.scanned += 1
            result.failed += 0 if ok else 1
        if user_ids:
            logger.info("Alert tick done: %d scanned, %d failed", result.scanned, result.failed)
        return result


async def alert_loop() -> None:
    from database import AsyncSessionLocal, engine

    while True:
        try:
            await run_due_scans(AsyncSessionLocal, engine)
        except Exception as exc:
            logger.error("Alert tick crashed: %s", type(exc).__name__)
        await asyncio.sleep(TICK_SECONDS)
