import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(title="SearchWork API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
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
