# SearchWork

Personal job-tracking app for UK graduate/junior developer roles.
CV upload → AI skill extraction → job search (Adzuna + Reed) → AI match scoring → application tracking.

## Active Learning Session

Bohdan is working through a Claude Code deep-dive curriculum using this project as a practice base.
**Current progress and next steps:** see `PROGRESS.md` in the project root.
**Full plan:** `~/.claude/plans/goofy-sauteeing-swan.md`

## Stack

- **Frontend:** Next.js + React + Tailwind CSS
- **Backend:** FastAPI (Python) + SQLAlchemy
- **Database:** PostgreSQL (Docker, managed manually)
- **AI:** Claude API (CV analysis + job match scoring)
- **Job APIs:** Adzuna, Reed.co.uk

## Dev Commands

**Frontend:**
```bash
cd frontend && npm run dev
```

**Backend:**
```powershell
cd "C:\Users\bogdy\OneDrive\Personal Files\Repos\SearchWork\backend"
.\venv\Scripts\activate
uvicorn main:app --reload
```

**Database (Docker):** managed manually by user — do not touch Docker config.

## Environment Variables

**backend/.env**
```
DATABASE_URL=
ANTHROPIC_API_KEY=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
REED_API_KEY=
RAPIDAPI_KEY=
```

**frontend/.env.local**
```
NEXT_PUBLIC_API_URL=
```

## Architecture

```
frontend/
├── app/                    # Next.js pages (layout, search, cv, applications)
├── components/
│   ├── applications/       # Application table, status tabs
│   ├── search/             # Job cards, search bar
│   ├── layout/             # Robot background, nav
│   └── ui/                 # Shared UI primitives
├── types/index.ts          # Shared TypeScript types
└── lib/                    # Client-side utilities

backend/
├── main.py                 # FastAPI app entry point
├── models.py               # SQLAlchemy DB models
├── schemas.py              # Pydantic request/response schemas
├── database.py             # DB connection
├── routers/                # Route handlers (applications, cv, jobs)
└── services/               # External integrations
    ├── ai_service.py       # Claude API (CV analysis + scoring)
    ├── adzuna_service.py   # Adzuna job search
    └── reed_service.py     # Reed.co.uk job search
```

## API Quirks

**Reed:** requires HTTP Basic Auth — `(REED_API_KEY, "")` as auth tuple. Endpoint: `https://www.reed.co.uk/api/1.0/search`. Returns `results` array; salary fields are `minimumSalary`/`maximumSalary` (can be null). Job URL: `https://www.reed.co.uk/jobs/{jobId}`.

**Adzuna:** query param auth — `app_id` + `app_key`. Endpoint: `https://api.adzuna.com/v1/api/jobs/gb/search/1`. Returns `results` array; salary fields are `salary_min`/`salary_max`. Rate limit: 250 req/hour on free tier.

**New job sources** (backend/services/ — untracked, experimental): arbeitnow, cwjobs, gradcracker, indeed, jobicy, jsearch, prospects, remotive, totaljobs, weworkremotely. Most use free public APIs or scraping — check each service file before wiring into jobs.py.

## Common Pitfalls

- **Async sessions:** never access a relationship without `selectinload()` — async SQLAlchemy raises `MissingGreenlet` at runtime, not at definition time.
- **datetime:** always use `datetime.now(timezone.utc).replace(tzinfo=None)` — `datetime.utcnow()` is deprecated and causes Pydantic v2 warnings.
- **Tests vs prod DB:** tests use SQLite in-memory; `JSONList` custom TypeDecorator bridges the difference. If adding a new column type, update `JSONList` logic or add a new TypeDecorator.
- **CORS:** frontend runs on :3000, backend on :8000. CORS is configured in `main.py` — if adding a new origin, update there.
- **CV file storage:** CV is stored as binary in the DB (not on disk). `cv_router` handles upload/retrieve via `application/octet-stream`.

## Test Commands

```powershell
cd backend
pytest tests/ -v                          # all tests
pytest tests/test_jobs_router.py -v       # job search tests
pytest tests/test_applications_router.py  # application CRUD
pytest tests/test_ai_service.py -v        # AI/Claude service
```

