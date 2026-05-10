import asyncio
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import CVProfile, SavedJob
from schemas import JobOut
from services import adzuna_service, reed_service
from services.ai_service import score_job_match

router = APIRouter()

async def get_cv_profile(db: AsyncSession) -> list[str]:
    result = await db.execute(select(CVProfile).order_by(CVProfile.id.desc()).limit(1))
    profile = result.scalar_one_or_none()
    if not profile:
        return []
    return profile.skills + profile.keywords

@router.get("/jobs", response_model=list[JobOut])
async def search_jobs(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    cv_skills = await get_cv_profile(db)

    adzuna_task = asyncio.create_task(adzuna_service.search_jobs(q))
    reed_task = asyncio.create_task(reed_service.search_jobs(q))
    adzuna_results, reed_results = await asyncio.gather(adzuna_task, reed_task, return_exceptions=True)
    adzuna_results = adzuna_results if isinstance(adzuna_results, list) else []
    reed_results = reed_results if isinstance(reed_results, list) else []
    all_jobs = adzuna_results + reed_results

    if not all_jobs:
        return []

    if not cv_skills:
        scores = [0] * len(all_jobs)
    else:
        scores = list(await asyncio.gather(*[
            score_job_match(cv_skills, job["description"]) for job in all_jobs
        ], return_exceptions=True))
        scores = [s if isinstance(s, int) else 0 for s in scores]

    saved = []
    for job_data, score in zip(all_jobs, scores):
        existing = await db.execute(
            select(SavedJob).where(
                SavedJob.external_id == job_data["external_id"],
                SavedJob.source == job_data["source"]
            )
        )
        job = existing.scalar_one_or_none()
        if job is None:
            job = SavedJob(**job_data, match_score=score)
            db.add(job)
        else:
            job.match_score = score
        saved.append(job)

    await db.commit()
    for job in saved:
        await db.refresh(job)

    return sorted(saved, key=lambda j: j.match_score, reverse=True)
