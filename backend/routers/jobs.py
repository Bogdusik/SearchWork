import asyncio
import logging
import re
from fastapi import APIRouter, Query, Depends, Request

logger = logging.getLogger(__name__)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth import get_current_user
from database import get_db
from models import CVProfile, User
from schemas import JobSearchResult

limiter = Limiter(key_func=get_remote_address)
from services import adzuna_service, reed_service, jsearch_service, remotive_service, weworkremotely_service, jobicy_service, arbeitnow_service, gradcracker_service, totaljobs_service, cwjobs_service, prospects_service, indeed_service
from services.ai_service import score_job_match

router = APIRouter()

DEFAULT_LOCATIONS = ["Glasgow", "Edinburgh", "Newcastle upon Tyne", "Leeds", "Manchester", "Liverpool"]

_NON_UK_LOCATION = re.compile(
    r'\b(USA|United States|U\.S\.A\.?|Canada|Australia|New Zealand|'
    r'Germany|France|Spain|Netherlands|Poland|Romania|India|'
    r'Pakistan|Singapore|Brazil|Mexico|Israel|Ukraine)\b',
    re.IGNORECASE,
)
_UK_LOCATION = re.compile(
    r'\b(UK|United Kingdom|England|Scotland|Wales|Britain|GB|'
    r'London|Manchester|Glasgow|Edinburgh|Leeds|Liverpool|'
    r'Birmingham|Bristol|Newcastle|Sheffield|Nottingham|'
    r'Reading|Oxford|Cambridge|Belfast|Cardiff|Aberdeen|Dundee|'
    r'Inverness|Stirling|Dumfries|Remote)\b',
    re.IGNORECASE,
)
_SENIOR_TITLE = re.compile(
    r'\b(senior|sr\.?|lead|principal|staff|head\s+of|director|architect|'
    r'manager|vp\s+of|vice\s+president|chief|cto|ceo|ciso)\b',
    re.IGNORECASE,
)

_INELIGIBLE = re.compile(
    r'(ILR\s+or\s+British\s+citizenship|must\s+hold\s+ILR|'
    r'British\s+citizenship\s+required|must\s+be\s+a\s+British\s+citizen|'
    r'hold\s+British\s+citizenship|'
    r'\bSC\s+cleared?\b|\bDV\s+cleared?\b|\bBPSS\s+cleared?\b|'
    r'security\s+clearance\s+required|active\s+(?:UK\s+)?security\s+clearance|'
    r'\d+[\s-]?year\s+(?:UK\s+)?security\s+(?:check|vetting|vet)|'
    r'PLEASE\s+NOTE\s+THAT\s+YOU\s+MUST\s+hold)',
    re.IGNORECASE,
)


def _is_uk_job(job: dict) -> bool:
    location = job.get("location", "").strip().lower()
    if not location or location in ("remote", "anywhere", "worldwide"):
        return True
    if _UK_LOCATION.search(job["location"]):
        return True
    if _NON_UK_LOCATION.search(job["location"]):
        return False
    return True


def _is_eligible(job: dict) -> bool:
    text = job.get("description", "") + " " + job.get("title", "")
    return not _INELIGIBLE.search(text)


def _is_junior_level(job: dict) -> bool:
    return not _SENIOR_TITLE.search(job.get("title", ""))


async def get_cv_profile(db: AsyncSession, user_id: int) -> list[str]:
    result = await db.execute(
        select(CVProfile)
        .where(CVProfile.user_id == user_id)
        .order_by(CVProfile.id.desc())
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return []
    return profile.skills + profile.keywords


async def _fetch_for_location(query: str, where: str) -> list[dict]:
    results = await asyncio.gather(
        adzuna_service.search_jobs(query, where=where),
        reed_service.search_jobs(query, location_name=where),
        jsearch_service.search_jobs(query, location=where),
        remotive_service.search_jobs(query, location=where),
        weworkremotely_service.search_jobs(query, location=where),
        jobicy_service.search_jobs(query, location=where),
        arbeitnow_service.search_jobs(query, location=where),
        gradcracker_service.search_jobs(query, location=where),
        totaljobs_service.search_jobs(query, location=where),
        cwjobs_service.search_jobs(query, location=where),
        prospects_service.search_jobs(query, location=where),
        indeed_service.search_jobs(query, location=where),
        return_exceptions=True,
    )
    jobs: list[dict] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Job service error for location %r: %s", where, result)
        elif isinstance(result, list):
            jobs += result
    return jobs


@router.get("/jobs", response_model=list[JobSearchResult])
@limiter.limit("10/minute")
async def search_jobs(
    request: Request,
    q: str = Query(..., min_length=1),
    locations: list[str] = Query(default=[]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cv_skills = await get_cv_profile(db, current_user.id)

    search_locations = locations if locations else DEFAULT_LOCATIONS
    location_results = await asyncio.gather(
        *[_fetch_for_location(q, loc) for loc in search_locations],
        return_exceptions=True,
    )

    seen: set[str] = set()
    all_jobs: list[dict] = []
    for result in location_results:
        if not isinstance(result, list):
            continue
        for job in result:
            key = f"{job['external_id']}:{job['source']}"
            if key not in seen:
                seen.add(key)
                all_jobs.append(job)

    all_jobs = [j for j in all_jobs if _is_uk_job(j) and _is_eligible(j) and _is_junior_level(j)]

    if not all_jobs:
        return []

    _empty_score = {"score": 0, "matched": [], "missing": []}
    if not cv_skills:
        score_results = [_empty_score] * len(all_jobs)
    else:
        raw_results = list(await asyncio.gather(
            *[score_job_match(cv_skills, job["description"]) for job in all_jobs],
            return_exceptions=True,
        ))
        score_results = [r if isinstance(r, dict) else _empty_score for r in raw_results]

    results = [
        JobSearchResult(
            **job_data,
            match_score=r["score"],
            matched_skills=r["matched"],
            missing_skills=r["missing"],
        )
        for job_data, r in zip(all_jobs, score_results)
    ]
    return sorted(results, key=lambda j: j.match_score, reverse=True)
