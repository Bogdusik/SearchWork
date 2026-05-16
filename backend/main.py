import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

_REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "ANTHROPIC_API_KEY",
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "REED_API_KEY",
    "SECRET_KEY",
]
_missing = [v for v in _REQUIRED_ENV_VARS if not os.getenv(v)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {_missing}")

from database import engine
import models
from routers import cv, jobs, applications, debug, auth_router

limiter = Limiter(key_func=get_remote_address)

_TABLES_NEEDING_USER_ID = ("cv_profiles", "saved_jobs", "cover_letters", "applications")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Create new tables (users, refresh_tokens, etc.); skips tables that already exist
        await conn.run_sync(models.Base.metadata.create_all)
        # Add user_id FK to pre-auth tables that already exist on the DB
        for table in _TABLES_NEEDING_USER_ID:
            await conn.execute(text(
                f"ALTER TABLE IF EXISTS {table} "
                f"ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
            ))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_saved_jobs_user_job "
            "ON saved_jobs(user_id, external_id, source)"
        ))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_cover_letters_user_job "
            "ON cover_letters(user_id, external_id, source)"
        ))
    yield

app = FastAPI(title="SearchWork API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(cv.router)
app.include_router(jobs.router)
app.include_router(applications.router)

if os.getenv("ENV") == "development":
    app.include_router(debug.router)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}


_LLMS_TXT = """# SearchWork API

AI-powered UK graduate job tracker. All endpoints require a Bearer token in the Authorization header unless noted.

## Authentication

POST /auth/register
  Body: {"email": "string", "password": "string (min 8 chars)"}
  Response: {"access_token": "string", "token_type": "bearer"}
  Sets httpOnly refresh_token cookie.

POST /auth/login
  Body: {"email": "string", "password": "string"}
  Response: {"access_token": "string", "token_type": "bearer"}
  Sets httpOnly refresh_token cookie.

POST /auth/refresh  (no Bearer required — uses refresh_token cookie)
  Response: {"access_token": "string", "token_type": "bearer"}
  Rotates the refresh token.

POST /auth/logout  (no Bearer required — uses refresh_token cookie)
  Response: 204 No Content
  Invalidates the refresh token.

GET /auth/me
  Response: {"id": int, "email": "string"}

GET /auth/google/url  (no Bearer required)
  Response: {"url": "string"}  — redirect the user here to start Google OAuth.

GET /auth/google/callback?code=&state=
  Exchanges the OAuth code, creates/links the user account, redirects to
  {FRONTEND_URL}/auth/callback?access_token=<jwt> with refresh_token cookie set.

## CV

GET /cv
  Response: CVProfile object or null if no CV uploaded yet.
  CVProfile: {"id": int, "skills": [str], "job_titles": [str], "keywords": [str], "updated_at": "ISO datetime"}

POST /cv  (multipart/form-data, field: "file")
  Accepts PDF or plain text. Extracts skills, job titles, and keywords via Claude AI.
  Response: CVProfile

POST /cv/review
  Body: {"target_role": "string"}
  Response: {"strengths": [str], "gaps": [str], "suggestions": [str], "overall": "string"}

POST /cv/cover-letter
  Body: {"external_id": "string", "source": "string", "job_title": "string", "company": "string",
         "description": "string", "force_regenerate": bool}
  Returns cached letter if one exists for (user, external_id, source) unless force_regenerate=true.
  Response: {"content": "string"}

## Jobs

GET /jobs?q=<query>&locations=<city>&locations=<city>
  Rate limited: 10/minute per IP.
  Searches Adzuna, Reed, JSearch, Remotive, WeWorkRemotely, Jobicy, Arbeitnow,
  Gradcracker, Totaljobs, CWJobs, Prospects, Indeed in parallel.
  Filters to UK-only, junior-level, no security clearance.
  Scores each job against CV skills via Claude AI.
  Response: list of JobSearchResult, sorted by match_score descending.
  JobSearchResult: {"external_id": str, "source": str, "title": str, "company": str,
    "location": str, "salary_min": int|null, "salary_max": int|null, "url": str,
    "description": str, "match_score": int (0-100), "matched_skills": [str], "missing_skills": [str]}

## Applications

GET /applications
  Response: list of Application (with nested job object), ordered by updated_at desc.
  Application: {"id": int, "status": str, "applied_at": str|null, "job": JobSearchResult}
  Status values: saved | in_progress | applied | interview | offer | rejected

POST /applications
  Body: {"job": JobSearchResult, "status": "string"}
  Creates a SavedJob record if not already saved, then creates an Application.
  Returns 409 if application already exists for this job.
  Response: Application

PATCH /applications/{app_id}
  Body: {"status": "string"}
  Updates application status. Sets applied_at when status becomes "applied".
  Response: Application

DELETE /applications/{app_id}
  Response: 204 No Content

## Utility

GET /           Response: {"status": "ok"}
GET /health     Response: {"status": "ok"}
GET /llms.txt   Response: this document (text/plain)
"""


@app.get("/llms.txt", response_class=PlainTextResponse, include_in_schema=False)
async def llms_txt():
    return _LLMS_TXT
