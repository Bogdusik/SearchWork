import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)

from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth import get_current_user
from database import get_db
from models import CVProfile, CoverLetter, User
from schemas import CVProfileOut, CVReviewRequest, CVReviewResponse, CoverLetterRequest
from services.cv_parser import extract_text_from_pdf
from services.ai_service import extract_cv_skills, generate_cv_review, generate_cover_letter

router = APIRouter(prefix="/cv", tags=["cv"])
limiter = Limiter(key_func=get_remote_address)

_PDF_MAGIC = b"%PDF"
_MAX_CV_BYTES = 10 * 1024 * 1024


@router.get("", response_model=CVProfileOut | None)
async def get_cv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CVProfile)
        .where(CVProfile.user_id == current_user.id)
        .order_by(CVProfile.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=CVProfileOut)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    header = await file.read(4)
    if header != _PDF_MAGIC:
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    rest = await file.read(_MAX_CV_BYTES)
    if len(rest) == _MAX_CV_BYTES and await file.read(1):
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
    pdf_bytes = header + rest

    raw_text = extract_text_from_pdf(pdf_bytes)
    extracted = await extract_cv_skills(raw_text)

    await db.execute(delete(CVProfile).where(CVProfile.user_id == current_user.id))
    profile = CVProfile(
        user_id=current_user.id,
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
@limiter.limit("5/minute")
async def review_cv(
    request: Request,
    body: CVReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CVProfile)
        .where(CVProfile.user_id == current_user.id)
        .order_by(CVProfile.updated_at.desc())
        .limit(1)
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
@limiter.limit("5/minute")
async def generate_cover_letter_endpoint(
    request: Request,
    body: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cached_result = await db.execute(
        select(CoverLetter).where(
            CoverLetter.user_id == current_user.id,
            CoverLetter.external_id == body.external_id,
            CoverLetter.source == body.source,
        )
    )
    cached = cached_result.scalar_one_or_none()

    if cached and not body.force_regenerate:
        return {"content": cached.content}

    profile_result = await db.execute(
        select(CVProfile)
        .where(CVProfile.user_id == current_user.id)
        .order_by(CVProfile.updated_at.desc())
        .limit(1)
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
            user_id=current_user.id,
            external_id=body.external_id,
            source=body.source,
            job_title=body.job_title,
            company=body.company,
            content=letter,
        ))
    await db.commit()
    return {"content": letter}
