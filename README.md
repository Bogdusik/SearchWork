# SearchWork

A personal job tracker built for UK graduate and junior developer roles. Upload your CV, let AI extract your skills and score job matches, search across multiple job boards, and track your applications — all in one place.

**Live:** https://searchwork-bogdusik.vercel.app

## Why It's Cool

- **AI-Powered CV Analysis** — Upload a PDF and Claude extracts your skills, experience, and target roles automatically. No manual tagging.
- **Multi-Source Job Search** — Searches Adzuna and Reed simultaneously, deduplicates results, and shows salary ranges where available
- **Match Scoring** — Claude scores each job against your CV profile so you know which applications are worth your time
- **Cover Letter Generation** — Generates tailored cover letters per job based on your CV and the job description
- **Application Tracker** — Kanban-style status tracking (Applied → Interview → Offer → Rejected) with full history
- **Dark Aesthetic UI** — Frosted glass cards, 3D robot background, Spotlight cursor effect, smooth Framer Motion animations

## Tech Stack

- **Frontend**: Next.js 14 App Router, React, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI (Python), SQLAlchemy 2.0 async, Pydantic v2
- **Database**: PostgreSQL (asyncpg)
- **AI**: Claude API (Anthropic) — CV parsing, job match scoring, cover letter generation
- **Job APIs**: Adzuna, Reed.co.uk
- **Deployment**: Vercel (frontend) + Railway (backend + PostgreSQL)

## Project Structure

```
SearchWork/
├── frontend/               # Next.js app
│   ├── app/                # Pages (cv, search, applications)
│   ├── components/         # UI components
│   └── lib/                # API client, utilities
├── backend/                # FastAPI app
│   ├── routers/            # Route handlers
│   ├── services/           # Claude API, Adzuna, Reed integrations
│   ├── models.py           # SQLAlchemy models
│   └── schemas.py          # Pydantic schemas
└── docker-compose.yml      # Local PostgreSQL
```

## How to Run Locally

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for PostgreSQL)
- Anthropic API key, Adzuna API credentials, Reed API key

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in your API keys
docker-compose up -d         # start PostgreSQL
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000

## Environment Variables

**backend/.env**
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/searchwork
ANTHROPIC_API_KEY=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
REED_API_KEY=
RAPIDAPI_KEY=
ALLOWED_ORIGINS=http://localhost:3000
```

**frontend/.env.local**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## What I Learned

- **Async SQLAlchemy in practice** — Working with `AsyncSession`, `selectinload`, and avoiding the common `MissingGreenlet` pitfalls that bite you at runtime
- **Claude API for real features** — Prompt engineering for structured extraction (skills, roles, scoring) rather than just chat completions
- **Full-stack deployment** — Wiring Vercel + Railway together, handling CORS across environments, and debugging Railway's Railpack build system
- **Multi-source API aggregation** — Normalising inconsistent job API responses (different salary field names, auth methods, rate limits) into a single schema
