import asyncio
import logging
import os
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AlertSettings, SeenJob
from routers import jobs as job_search
from services import ntfy_service
from services.ai_service import score_job_match
from utils import _utcnow

logger = logging.getLogger(__name__)

MAX_INDIVIDUAL_PUSHES = 5
MAX_CONCURRENT_SCORING = 5
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@dataclass
class ScanResult:
    skipped_no_cv: bool = False
    baseline: bool = False
    fetched: int = 0
    scored: int = 0
    failed_scoring: int = 0
    matches: int = 0


def _job_key(job: dict) -> tuple[str, str]:
    return (str(job["external_id"]), job["source"])


def _format_salary(job: dict) -> str | None:
    low, high = job.get("salary_min"), job.get("salary_max")
    if low and high and low != high:
        return f"£{low:,}–£{high:,}"
    if low or high:
        return f"£{(low or high):,}"
    return None


def _push_message(job: dict, score: int) -> str:
    parts = [f"Match {score}%", job.get("location") or None, _format_salary(job)]
    return " · ".join(p for p in parts if p)


async def _seen_keys(db: AsyncSession, user_id: int) -> set[tuple[str, str]]:
    rows = await db.execute(select(SeenJob.external_id, SeenJob.source).where(SeenJob.user_id == user_id))
    return {(external_id, source) for external_id, source in rows.all()}


async def _send(user_id: int, **push_kwargs) -> None:
    try:
        await ntfy_service.send_push(**push_kwargs)
    except ntfy_service.NtfyError as exc:
        logger.warning("Alert push failed for user %s: %s", user_id, exc)


async def scan_user(db: AsyncSession, settings: AlertSettings) -> ScanResult:
    user_id = settings.user_id
    result = ScanResult()

    cv_skills = await job_search.get_cv_profile(db, user_id)
    if not cv_skills:
        result.skipped_no_cv = True
        return result

    jobs = await job_search.collect_filtered_jobs(settings.query, settings.locations)
    result.fetched = len(jobs)

    seen = await _seen_keys(db, user_id)
    unseen = [job for job in jobs if _job_key(job) not in seen]

    if settings.baseline_at is None:
        # First scan for this search: remember what is already on the boards so only jobs posted later
        # trigger pushes. Marked done even with zero jobs, so a narrow query's first real hit is pushed.
        db.add_all(SeenJob(user_id=user_id, external_id=k[0], source=k[1]) for k in map(_job_key, unseen))
        settings.baseline_at = _utcnow()
        await db.commit()
        result.baseline = True
        return result

    limit = asyncio.Semaphore(MAX_CONCURRENT_SCORING)

    async def score(job: dict) -> dict:
        async with limit:
            return await score_job_match(cv_skills, job["description"])

    outcomes = await asyncio.gather(*[score(job) for job in unseen], return_exceptions=True)
    scored: list[tuple[dict, int]] = []
    for job, outcome in zip(unseen, outcomes):
        if isinstance(outcome, BaseException):
            result.failed_scoring += 1
            continue
        scored.append((job, outcome["score"]))
    if result.failed_scoring:
        logger.warning("Alert scan for user %s: %d jobs failed scoring, retrying next scan",
                       user_id, result.failed_scoring)

    db.add_all(SeenJob(user_id=user_id, external_id=k[0], source=k[1]) for k in (_job_key(j) for j, _ in scored))
    await db.commit()
    result.scored = len(scored)

    matches = sorted((pair for pair in scored if pair[1] >= settings.min_score), key=lambda p: p[1], reverse=True)
    result.matches = len(matches)

    for job, score in matches[:MAX_INDIVIDUAL_PUSHES]:
        await _send(
            user_id,
            topic=settings.ntfy_topic,
            title=f"{job['title']} at {job['company']}",
            message=_push_message(job, score),
            click_url=job["url"],
            tags=["briefcase"],
        )

    extra = len(matches) - MAX_INDIVIDUAL_PUSHES
    if extra > 0:
        await _send(
            user_id,
            topic=settings.ntfy_topic,
            title=f"+{extra} more matches in SearchWork",
            message=f"{extra} more new jobs scored {settings.min_score}% or higher.",
            click_url=f"{FRONTEND_URL}/search",
            tags=["briefcase"],
        )

    return result
