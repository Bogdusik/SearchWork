import logging
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from models import CVProfile, CoverLetter
from schemas import CVProfileOut, CVReviewRequest, CVReviewResponse, CoverLetterRequest
from services.cv_parser import extract_text_from_pdf
from services.ai_service import extract_cv_skills, generate_cv_review, generate_cover_letter

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

    try:
        review = await generate_cv_review(profile.raw_text, body.target_role)
        return review
    except Exception as e:
        logger.error("CV review failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="CV review failed. Please try again.")


@router.post("/cover-letter")
async def generate_cover_letter_endpoint(
    body: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Return cached cover letter if available, otherwise generate and cache it."""
    cached_result = await db.execute(
        select(CoverLetter).where(
            CoverLetter.external_id == body.external_id,
            CoverLetter.source == body.source,
        )
    )
    cached = cached_result.scalar_one_or_none()

    if cached and not body.force_regenerate:
        return {"content": cached.content}

    profile_result = await db.execute(
        select(CVProfile).order_by(CVProfile.updated_at.desc()).limit(1)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=400, detail="Upload a CV first.")

    try:
        letter = await generate_cover_letter(
            profile.raw_text, body.job_title, body.company, body.description
        )
    except Exception as e:
        logger.error("Cover letter generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Cover letter generation failed. Please try again.")

    if cached:
        cached.content = letter
        cached.created_at = datetime.now()
    else:
        db.add(CoverLetter(
            external_id=body.external_id,
            source=body.source,
            job_title=body.job_title,
            company=body.company,
            content=letter,
        ))
    await db.commit()
    return {"content": letter}
