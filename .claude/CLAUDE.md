# SearchWork

Personal job-tracking app for UK graduate/junior developer roles.
CV upload → AI skill extraction → job search (Adzuna + Reed) → AI match scoring → application tracking.
Deploy: Vercel (web), Railway (api + db).

## Active Learning Session

Bohdan is working through a Claude Code deep-dive curriculum using this project as a practice base.
**Current progress and next steps:** see `PROGRESS.md` in the project root (kept locally, not committed).
**Full plan:** `~/.claude/plans/goofy-sauteeing-swan.md`

## Stack

- **Frontend:** Next.js + React + Tailwind CSS
- **Backend:** FastAPI (Python) + SQLAlchemy
- **Database:** PostgreSQL (Docker, managed manually)
- **AI:** Claude API (CV analysis + job match scoring)
- **Job APIs:** Adzuna, Reed.co.uk

## Layout
- `frontend/` Next.js 16 App Router app (`app/`, `components/`, `lib/api.ts`), Playwright mobile tests in `frontend/tests/mobile`
- `backend/` FastAPI app, flat layout (`main.py`, `routers/`, `services/`, `models.py`, `schemas.py`), tests in `backend/tests` (SQLite via `conftest.py`)
- `docs/specs/` active specs (temporary, deleted on close), `docs/media/` README assets
- `evals/` + `scripts/` deterministic checks and tooling
- `docker-compose.yml` local PostgreSQL 16 (`db` service)

## Commands
Always use `just`. Do not guess raw commands.
- `just dev-web` / `just dev-api` run locally (`dev-api` needs `backend/venv`)
- `just lint` (frontend ESLint), `just typecheck`, `just test` (backend pytest), `just build`, `just e2e` (Playwright mobile)
- `just evals fast` quick gate (lint, types, backend tests)
- `just evals full` fast + build + e2e

**Database (Docker):** managed manually by user — do not touch Docker config.

## Environment Variables

Names only. Which flows need each one, where the values come from and the local defaults: `docs/verify-env.md` section 4. Templates: `backend/.env.example`, `frontend/.env.local.example`.

**backend/.env**
```
# required: main.py refuses to start if any is empty
DATABASE_URL=
SECRET_KEY=
ANTHROPIC_API_KEY=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
REED_API_KEY=

# optional
RAPIDAPI_KEY=
ENV=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
FRONTEND_URL=
ALLOWED_ORIGINS=
NTFY_URL=
ALERT_SCAN_INTERVAL_HOURS=
ALERT_SCHEDULER_ENABLED=
```

`POSTGRES_PASSWORD` is listed in `backend/.env.example` but the backend never reads it. Docker Compose takes it from the shell.

**frontend/.env.local** (optional locally)
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

## Hard rules
- Never commit, push, amend, reset or rebase unless I explicitly ask.
- Never say work is done without a passing `just evals fast` in this session. Show the result.
- Never read, print or commit secrets. `.env*` is off limits, `.env.example` is fine.
- Never weaken a test to make it pass. Fix the code, or tell me the test is wrong and why.
- Do not touch files outside the task scope. Do not overwrite my uncommitted edits.
- Tests use synthetic data only. No real CVs, emails or tokens in fixtures.

## Code style
- Self-documenting names. Comment only the non-obvious "why".
- No spec ids (AC1, P2) in code or comments.
- Smallest change that satisfies the task. No drive-by refactors.

## Stop conditions (write a blocker, do not improvise)
- 3 failed repair attempts on one task
- missing secret, service or access
- product decision is unclear and the code cannot answer it
- the change needs work outside the agreed scope

## Workflow: pick a track by risk
| Change | Track |
|---|---|
| No behavior change (rename, typo, formatting) | Just do it, run `just evals fast` |
| Small, low risk, one package | `/spec` short, then `/implement` |
| Auth, tokens, user data, migrations, anything public-facing | `/spec` full, `/implement`, `/spec-review`, `/verify` |

Flow: `/spec` -> I approve -> `/implement <spec>` -> `/spec-review` -> `/verify` -> I approve -> close.
Close = move 3-5 lines of outcome into `docs/CHANGELOG.md`, delete the spec.
"Implemented" and "deployed" are different. Never write "deployed" unless I confirmed a deploy.

