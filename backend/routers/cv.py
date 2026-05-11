from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models import CVProfile
from schemas import CVProfileOut, CVReviewRequest, CVReviewResponse
from services.cv_parser import extract_text_from_pdf
from services.ai_service import extract_cv_skills, generate_cv_review

router = APIRouter(prefix="/cv", tags=["cv"])


@router.get("", response_model=CVProfileOut | None)
async def get_cv(db: AsyncSession = Depends(get_db)):
    """Return the most recent CV profile, or null if none exists."""
    result = await db.execute(
        select(CVProfile).order_by(CVProfile.updated_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=CVProfileOut)
async def upload_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF CV, extract text and skills via AI, and replace any existing profile."""
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text = extract_text_from_pdf(pdf_bytes)
    extracted = await extract_cv_skills(raw_text)

    # Delete all existing profiles, then insert a fresh one
    await db.execute(delete(CVProfile))
    profile = CVProfile(
        raw_text=raw_text,
        skills=extracted.get("skills", []),
        job_titles=extracted.get("job_titles", []),
        keywords=extracted.get("keywords", []),
    )
    db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/review", response_model=CVReviewResponse)
async def review_cv(
    body: CVReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a structured CV review via Claude for the stored CV profile."""
    result = await db.execute(
        select(CVProfile).order_by(CVProfile.updated_at.desc()).limit(1)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="No CV uploaded yet.")

    review = await generate_cv_review(profile.raw_text, body.target_role)
    return review
