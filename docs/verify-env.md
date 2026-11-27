# Verify environment

How `/verify` runs SearchWork locally. If a fact here proves wrong, report it under "Knowledge updates" in the verify report.

## Hard rules

- **Local only.** Never run `/verify` against the deployed app (Vercel frontend, Railway API or Railway database). Every URL used must start with `http://localhost`.
- **Never touch Docker.** Do not start, stop, restart or inspect containers, and do not run `docker` or `docker compose`. The user starts the database.
- **Database down = blocker.** If the check below fails, stop, mark every criterion `Not tested` with the reason "local database not running", and ask the user to start it.
- **Never read `backend/.env`** or any other `.env*` file. Do not print environment values.

## 1. Database (user starts it)

The user runs this from the repo root:

```bash
POSTGRES_PASSWORD=postgres docker compose up -d db
```

PostgreSQL 16 on `127.0.0.1:5432`, database `searchwork`.

`/verify` only checks that it is reachable:

```bash
nc -z 127.0.0.1 5432 && echo "db up" || echo "db down"
```

## 2. Backend

```bash
just dev-api        # cd backend && venv/bin/uvicorn main:app --reload
```

- API: http://localhost:8000
- Health: http://localhost:8000/health returns `{"status": "ok"}`
- Swagger UI: http://localhost:8000/docs, API reference: http://localhost:8000/llms.txt

The user creates `backend/.env`. The app refuses to start unless `DATABASE_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` and `REED_API_KEY` are all set. If startup fails with `Missing required environment variables`, that is a blocker for the user, not something to fix.

`/verify` may start the backend itself and must stop it before finishing. It must not stop a backend the user started.

## 3. Frontend

```bash
just dev-web        # cd frontend && npm run dev
```

- App: http://localhost:3000
- Login page: http://localhost:3000/login

`frontend/.env.local` is optional locally: `frontend/lib/api.ts` falls back to `http://localhost:8000`.

## 4. Environment variables and the flows that need them

**Startup gate:** `backend/main.py` refuses to start if any of the six variables marked **required** is empty. A non-empty placeholder passes the gate, so a key you do not have yet can stay as the `.env.example` placeholder. Only the flows that call that service break.

| Variable | File | Needed by | Where to get the value | Missing or placeholder in `/verify` |
|---|---|---|---|---|
| `DATABASE_URL` **required** | `backend/.env` | everything (auth, CV upload, job search, applications) | Local: `postgresql+asyncpg://postgres:postgres@localhost:5432/searchwork` (password matches `POSTGRES_PASSWORD=postgres` in section 1). Use `localhost`, not `127.0.0.1`: `database.py` turns on SSL for any URL without the string `localhost`, and local Postgres has no SSL. | Blocker. All criteria `Not tested` ("backend cannot start / database unreachable") |
| `SECRET_KEY` **required** | `backend/.env` | auth: JWT signing, Google OAuth `state` | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` | Blocker. All criteria `Not tested` ("backend cannot start") |
| `ANTHROPIC_API_KEY` **required** | `backend/.env` | CV upload (`POST /cv`, skill extraction), CV review, cover letter, match scoring in job search | Claude Console (platform.claude.com, formerly console.anthropic.com) → API keys | Placeholder: `Not tested` for CV upload, CV review, cover letter and any match-score criterion. See the note below. |
| `ADZUNA_APP_ID` **required** | `backend/.env` | job search (Adzuna source) | developer.adzuna.com → register → dashboard shows App ID and key | Placeholder: `Not tested` only for criteria that name Adzuna results. Search still returns jobs from the free sources. |
| `ADZUNA_APP_KEY` **required** | `backend/.env` | job search (Adzuna source) | same as above | same as above |
| `REED_API_KEY` **required** | `backend/.env` | job search (Reed source) | reed.co.uk/developers → request a Jobseeker API key | Placeholder: `Not tested` only for criteria that name Reed results |
| `RAPIDAPI_KEY` | `backend/.env` | job search (JSearch source only) | rapidapi.com → subscribe to the JSearch API (free tier) → `X-RapidAPI-Key` | Optional. Empty means the source is skipped silently. Never a reason for `Not tested`. |
| `ENV` | `backend/.env` | auth cookies, debug router | Set `development` locally | Optional locally. `development` gives a non-`Secure`, `SameSite=Lax` refresh cookie and mounts the debug router. Any other value makes the cookie `Secure; SameSite=None`. |
| `GOOGLE_CLIENT_ID` | `backend/.env` | auth: Google sign-in only | Google Cloud Console → APIs & Services → Credentials → OAuth client ID (Web application) | Google sign-in is out of scope (section 5). Empty: `/auth/google/url` returns 503. Mark `Not tested`. |
| `GOOGLE_CLIENT_SECRET` | `backend/.env` | auth: Google sign-in only | same OAuth client | same as above |
| `GOOGLE_REDIRECT_URI` | `backend/.env` | auth: Google sign-in only | `http://localhost:8000/auth/google/callback`, also added as an authorised redirect URI on the OAuth client | Default is the same value. Never a reason for `Not tested`. |
| `FRONTEND_URL` | `backend/.env` | auth: redirect after Google sign-in; click link of the "+N more matches" alert push | `http://localhost:3000` | Default is the same value |
| `ALLOWED_ORIGINS` | `backend/.env` (not in `.env.example`) | CORS for every browser call | Leave unset locally. The default is `http://localhost:3000`. | Default is fine locally |
| `NTFY_URL` | `backend/.env` (commented out in `.env.example`) | job alerts: push delivery | Leave unset to use `https://ntfy.sh`, or a self-hosted ntfy URL | Optional. Default is public ntfy.sh. Pushes to a topic can be checked live in the browser at `https://ntfy.sh/<topic>`. |
| `ALERT_SCAN_INTERVAL_HOURS` | `backend/.env` | job alerts: how old `last_scan_at` must be before a user is scanned again | Leave unset (6). For a live check set a small value such as `0.05` (3 minutes). | Optional. Accepts decimals. The loop itself always ticks every 15 minutes and once at startup. |
| `ALERT_SCHEDULER_ENABLED` | `backend/.env` | job alerts: background scan loop | Leave unset (on). `false` turns the loop off; the `/alerts` endpoints still work. | Optional. With the loop on, starting the backend scans every enabled, due user right away and calls the job sources and Claude. |
| `POSTGRES_PASSWORD` | `backend/.env.example` | nothing in the backend code | Docker Compose reads it from the shell or a root `.env`, not from `backend/.env` (see section 1) | Not read by the app |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | every frontend call (`lib/api.ts`, `lib/auth-context.tsx`) and the CSP `connect-src` (`next.config.ts`) | `http://localhost:8000` | Optional. The fallback is the same value. |

These work with placeholder keys: register, login, refresh, logout, `/auth/me`, and the applications tracker (`/applications` CRUD with a synthetic job body).

`/verify` cannot see whether keys are real, because it never reads `.env`. How a placeholder key shows up at runtime:

- **CV upload** (`POST /cv`): the Anthropic error is not caught, so the endpoint returns 500. CV review and cover letter return 500 with "... failed. Please try again."
- **Match scoring** (`GET /jobs`): Anthropic errors are swallowed and every job gets `match_score: 0` with empty `matched_skills`. If a CV is uploaded and every score is 0, treat the Anthropic key as a placeholder.
- **Adzuna / Reed**: each source fails independently. The error appears in the backend log as `Job service error`. The search still returns jobs from the keyless sources (Remotive, Jobicy, Arbeitnow and others), so an empty Adzuna or Reed result list is not a failure of the search.

In these cases mark the affected criteria `Not tested` with the reason "API keys missing or placeholder". Do not mark them `Fail`.

Rate limits: `/jobs` allows 10 requests a minute, and `/auth/register` and `/auth/login` allow 20 a minute each, per client IP.

## 5. Test account (synthetic, local database only)

| Field | Value |
|---|---|
| Email | `verify@example.com` |
| Password | `verify-local-only-1` |

Create it once on the local database. A `409 Email already registered` means it already exists:

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"verify@example.com","password":"verify-local-only-1"}'
```

Log in through the UI at http://localhost:3000/login with email and password, or through the API:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"verify@example.com","password":"verify-local-only-1"}'
```

The response has `access_token` (send it as `Authorization: Bearer <token>`) and sets an httpOnly `refresh_token` cookie scoped to `/auth/refresh`.

Notes:
- The address uses `example.com` (reserved, never delivers mail). `.test` addresses are rejected by the backend's email validation with a 422.
- Google sign-in is out of scope for `/verify`: it needs a real Google account.
- All data created for verification is synthetic: fictional job titles and companies, no real CVs. For CV upload use `backend/tests/fixtures/sample_cv.pdf` (synthetic one-page PDF, text "Python developer React", no personal data).
