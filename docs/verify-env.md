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

## 4. Flows that need real API keys

| Flow | Endpoint | Needs |
|---|---|---|
| CV upload and skill extraction | `POST /cv` | Anthropic key |
| CV review | `POST /cv/review` | Anthropic key |
| Cover letter | `POST /cv/cover-letter` | Anthropic key |
| Job search and match scoring | `GET /jobs` | Adzuna and Reed keys, Anthropic key |

These work without keys: register, login, refresh, logout, `/auth/me`, and the applications tracker (`/applications` CRUD with a synthetic job body).

`/verify` cannot see whether keys are real, because it never reads `.env`. When a key-dependent flow fails with an upstream or authentication error (5xx from `/cv`, an Anthropic or Adzuna/Reed auth error in the backend log, or a search that fails on every source), mark those criteria `Not tested` with the reason "API keys missing or placeholder". Do not mark them `Fail`.

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
