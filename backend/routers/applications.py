from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import Application, SavedJob
from schemas import ApplicationOut, ApplicationCreate, ApplicationUpdate

router = APIRouter()


@router.get("/applications", response_model=list[ApplicationOut])
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .order_by(Application.updated_at.desc())
    )
    return result.scalars().all()


@router.post("/applications", response_model=ApplicationOut)
async def create_application(body: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    job = await db.get(SavedJob, body.job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    existing = await db.execute(select(Application).where(Application.job_id == body.job_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Application for this job already exists")
    applied_at = datetime.now(timezone.utc) if body.status == "applied" else None
    app = Application(job_id=body.job_id, status=body.status, applied_at=applied_at)
    db.add(app)
    await db.commit()
    result = await db.execute(
        select(Application).options(selectinload(Application.job)).where(Application.id == app.id)
    )
    return result.scalar_one()


@router.patch("/applications/{app_id}", response_model=ApplicationOut)
async def update_application(app_id: int, body: ApplicationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application).options(selectinload(Application.job)).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = body.status
    if body.status == "applied":
        if not app.applied_at:
            app.applied_at = datetime.now(timezone.utc)
    else:
        app.applied_at = None
    await db.commit()
    # Re-query with selectinload to ensure job relationship is loaded
    result = await db.execute(
        select(Application).options(selectinload(Application.job)).where(Application.id == app_id)
    )
    return result.scalar_one()
