# SearchWork

A personal job tracker built for UK graduate and junior developer roles. Upload your CV, let AI extract your skills and score job matches, search across 12 job boards simultaneously, generate tailored cover letters, and track your applications — all in one place.

**Live demo:** https://searchwork-bogdusik.vercel.app

---

## Features

- **AI-Powered CV Analysis** — Upload a PDF and Claude (Anthropic) extracts your skills, experience, and target roles automatically
- **Multi-Source Job Search** — Searches Adzuna, Reed, JSearch, Remotive, WeWorkRemotely, Jobicy, Arbeitnow, Gradcracker, Totaljobs, CWJobs, Prospects, and Indeed simultaneously; deduplicates results; filters to UK-only junior roles
- **AI Match Scoring** — Claude scores each job against your CV profile (0–100%) with matched and missing skills breakdown
- **Cover Letter Generation** — Generates and caches tailored cover letters per job; supports regeneration
- **CV Analysis** — Full ATS review with critical issues, structural feedback, and a prioritised action table
- **Application Tracker** — Status tracking (Saved → In Progress → Applied → Interview → Offer → Rejected) with stats overview
- **JWT + Google OAuth Auth** — Access token stored in memory (XSS-safe), refresh token in httpOnly cookie, 7-day rotation
- **Dark UI** — Frosted glass cards, Spline 3D robot background, Spotlight cursor, skip-to-content, full keyboard navigation

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 App Router, React, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python), SQLAlchemy 2.0 async, Pydantic v2 |
| Database | PostgreSQL (asyncpg) |
| AI | Claude API (Anthropic) — CV parsing, match scoring, cover letter generation |
| Auth | JWT (PyJWT) + Google OAuth 2.0, bcrypt password hashing |
| Rate limiting | slowapi |
| Deployment | Vercel (frontend) + Railway (backend + PostgreSQL) |

---

## Project Structure

```
SearchWork/
├── frontend/
│   ├── app/                    # Next.js pages + route layouts (metadata)
│   │   ├── applications/
│   │   ├── auth/callback/
│   │   ├── cv/
│   │   ├── login/
│   │   └── search/
│   ├── components/
│   │   ├── applications/       # ApplicationRow, StatusTabs
│   │   ├── cv/                 # UploadZone, SkillsDisplay, CvReview
│   │   ├── dashboard/          # StatsRow
│   │   ├── layout/             # Navbar, RobotBackground
│   │   ├── search/             # JobCard, SearchBar
│   │   └── ui/                 # ErrorBoundary, Toast, Skeleton, CoverLetterModal, …
│   └── lib/                    # api.ts, auth-context.tsx, constants.ts, search-store.ts
├── backend/
│   ├── routers/                # auth_router, applications, cv, jobs
│   ├── services/               # ai_service, adzuna, reed, jsearch, remotive, …
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # JWT helpers
│   └── utils.py                # Shared utilities (_utcnow)
└── docker-compose.yml          # Local PostgreSQL
```

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for local PostgreSQL)
- API keys: Anthropic, Adzuna, Reed (see Environment Variables below)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # fill in your keys
docker-compose up -d         # start PostgreSQL
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
# → http://localhost:8000/llms.txt  (LLM-readable API docs)
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev
# → http://localhost:3000
```

---

## Environment Variables

### `backend/.env`

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/searchwork
SECRET_KEY=your-secret-key-min-32-chars
ANTHROPIC_API_KEY=sk-ant-...
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
REED_API_KEY=
RAPIDAPI_KEY=                # for JSearch
ALLOWED_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
GOOGLE_CLIENT_ID=            # optional — enables Google OAuth
GOOGLE_CLIENT_SECRET=        # optional
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
ENV=development              # removes Secure flag from cookies locally
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API

Full machine-readable docs at [`/llms.txt`](https://searchwork-bogdusik.vercel.app/llms.txt) (for LLMs) and interactive Swagger UI at `/docs`.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Email/password login |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `GET` | `/auth/google/url` | Start Google OAuth flow |
| `GET` | `/cv` | Fetch parsed CV profile |
| `POST` | `/cv` | Upload and analyse CV (PDF) |
| `POST` | `/cv/review` | Full ATS review for a target role |
| `POST` | `/cv/cover-letter` | Generate (or fetch cached) cover letter |
| `GET` | `/jobs?q=&locations=` | Search + AI-score jobs across all sources |
| `GET` | `/applications` | List saved applications |
| `POST` | `/applications` | Save a job as an application |
| `PATCH` | `/applications/{id}` | Update application status |
| `DELETE` | `/applications/{id}` | Remove application |

---

## What I Learned

- **Async SQLAlchemy in production** — `AsyncSession`, `selectinload`, avoiding `MissingGreenlet` pitfalls
- **Claude API for structured extraction** — prompt engineering for skills, scoring, and review rather than generic chat
- **Multi-source API aggregation** — normalising 12 inconsistent job APIs (different auth methods, salary fields, rate limits) into a single schema
- **Full-stack deployment** — Vercel + Railway, cross-environment CORS, Railway Railpack build system
- **XSS-safe auth** — access token in memory (module-level variable) instead of localStorage; refresh token in httpOnly cookie
- **Accessibility** — WCAG 2.1 patterns: combobox keyboard nav, focus traps, skip links, `aria-live` regions, `role="tab"` patterns
