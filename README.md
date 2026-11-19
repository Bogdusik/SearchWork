<div align="center">

<img src="docs/media/demo.gif" alt="Searching for graduate software engineer roles: results arrive sorted by AI match score, the reasoning expands to show matched and missing skills, a tailored cover letter opens, then the application tracker" width="860">

# SearchWork

**One search across 11 UK job boards. Claude reads your CV, scores every vacancy against it and writes the cover letter.**

[![CI](https://github.com/Bogdusik/SearchWork/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Bogdusik/SearchWork/actions/workflows/ci.yml)
[![Live demo](https://img.shields.io/badge/live_demo-searchwork-818cf8?logo=vercel&logoColor=white)](https://searchwork-bogdusik.vercel.app)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude-API-D97757?logo=anthropic&logoColor=white)
[![License: MIT](https://img.shields.io/badge/license-MIT-2EA44F)](LICENSE)

[Live demo](https://searchwork-bogdusik.vercel.app) · [How a search works](#how-a-search-works) · [Run it locally](#running-locally) · [API](#api)

</div>

I built SearchWork for my own graduate job search. Job boards each show a slice of the market, most "graduate" listings are not, and reading a hundred adverts to find the ten that fit is slow. SearchWork asks all the boards at once, drops what I can't apply for and ranks the rest by how well they match my CV.

<sub>Screenshots and the GIF use a fictional demo profile and made-up companies.</sub>

## What it does

<table>
<tr>
<td width="50%" valign="top">
<img src="docs/media/search.png" alt="Job search results sorted by match score, with the first card expanded to show matched skills in green and a missing skill in red"><br>
<b>Search and rank.</b> One query fans out to 11 job sources across your chosen cities. Results come back deduplicated, filtered to UK junior roles and sorted by AI match score. "Why this score?" shows the matched and missing skills.
</td>
<td width="50%" valign="top">
<img src="docs/media/cover-letter.png" alt="Cover letter side panel generated for a graduate backend role, with copy and regenerate buttons"><br>
<b>Cover letter in one click.</b> Claude writes a letter from your CV and the advert. It is cached per job, so reopening it is free; Regenerate asks for a new one.
</td>
</tr>
<tr>
<td width="50%" valign="top">
<img src="docs/media/cv-review.png" alt="CV analysis for a target role: summary, critical, structural and polish issues, and a priority table with impact labels"><br>
<b>CV review for a target role.</b> An ATS-style review grouped into critical, structural and polish issues, with a prioritised action table.
</td>
<td width="50%" valign="top">
<img src="docs/media/applications.png" alt="Application tracker with totals, status tabs and rows showing match score, skills and status"><br>
<b>Application tracker.</b> Save a job and move it through Saved → In Progress → Applied → Interview → Offer / Rejected, with totals at the top.
</td>
</tr>
</table>

<details>
<summary><b>More screens</b>: CV profile and sign-in</summary>
<br>
<p>
  <img src="docs/media/cv-profile.png" alt="CV profile page with skills and target roles extracted from the uploaded PDF" width="49%">
  <img src="docs/media/login.png" alt="Sign-in page over the 3D robot background, with email and Google sign-in" width="49%">
</p>
</details>

## How a search works

```mermaid
flowchart TB
  Q["GET /jobs · query + cities"] --> A1 & A2 & A3

  subgraph F["11 sources × every city, in parallel"]
    A1["Adzuna · Reed · JSearch"]
    A2["Remotive · WeWorkRemotely<br/>Jobicy · Arbeitnow"]
    A3["Gradcracker · Totaljobs<br/>CWJobs · Prospects"]
  end

  A1 & A2 & A3 --> D["Deduplicate by external_id + source"]
  D --> X["Filter in code<br/>UK only · junior titles · no clearance or citizenship requirement"]
  X --> S["Claude scores each job against the CV, in parallel"]
  CV[("PostgreSQL<br/>parsed CV profile")] -.-> S
  S --> R["Sorted by match %, with matched and missing skills"]
```

- **One failing source never breaks a search.** Every source runs under `asyncio.gather(..., return_exceptions=True)`; a source that errors is logged and skipped.
- **Filters run in code, not in the prompt.** Senior titles, non-UK locations and adverts that require security clearance or British citizenship are removed before anything is sent to Claude, so no tokens are spent on jobs I can't apply for.
- **Rate limited.** `/jobs` is limited to 10 requests a minute per client with slowapi, because one search can mean hundreds of upstream calls.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, Framer Motion, Spline 3D |
| Backend | FastAPI, SQLAlchemy 2.0 async, Pydantic v2, slowapi |
| Database | PostgreSQL 16 (asyncpg) |
| AI | Claude API: CV parsing, match scoring, CV review, cover letters |
| Auth | JWT (PyJWT) + Google OAuth 2.0, bcrypt; access token in memory, refresh token in an httpOnly cookie |
| Tests and CI | pytest (backend), type-check and build (frontend), Playwright mobile layout tests; GitHub Actions on every push |
| Deployment | Vercel (frontend), Railway (backend + PostgreSQL) |

<details>
<summary><b>Project structure</b></summary>

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
│   ├── lib/                    # api.ts, auth-context.tsx, constants.ts, search-store.ts
│   └── tests/mobile/           # Playwright layout tests
├── backend/
│   ├── routers/                # auth_router, applications, cv, jobs
│   ├── services/               # ai_service, cv_parser and one module per job source
│   ├── tests/                  # pytest
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   └── auth.py                 # JWT helpers
├── docs/media/                 # README screenshots and GIF
└── docker-compose.yml          # Local PostgreSQL
```

</details>

## Running locally

**You need:** Python 3.11+, Node.js 20+, Docker Desktop, and API keys for Anthropic, Adzuna and Reed (JSearch is optional).

**Database** (from the repo root)

```bash
POSTGRES_PASSWORD=postgres docker compose up -d   # PostgreSQL 16 on localhost:5432
```

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # fill in your keys
uvicorn main:app --reload
```

The API runs on http://localhost:8000, with Swagger UI at `/docs` and LLM-readable docs at `/llms.txt`.

**Frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000.

**Tests**

```bash
cd backend && python -m pytest -q
cd frontend && npm run test:mobile
```

<details>
<summary><b>Environment variables</b></summary>

`backend/.env`

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
GOOGLE_CLIENT_ID=            # optional, enables Google OAuth
GOOGLE_CLIENT_SECRET=        # optional
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
ENV=development              # removes the Secure flag from cookies locally
```

`frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

</details>

## API

Full machine-readable docs are at [`/llms.txt`](https://searchwork-bogdusik.vercel.app/llms.txt), and Swagger UI is at `/docs`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Email and password login |
| `POST` | `/auth/refresh` | Rotate the refresh token |
| `GET` | `/auth/google/url` | Start the Google OAuth flow |
| `GET` | `/cv` | Fetch the parsed CV profile |
| `POST` | `/cv` | Upload and analyse a CV (PDF) |
| `POST` | `/cv/review` | Full ATS review for a target role |
| `POST` | `/cv/cover-letter` | Generate (or fetch the cached) cover letter |
| `GET` | `/jobs?q=&locations=` | Search and AI-score jobs across all sources |
| `GET` | `/applications` | List saved applications |
| `POST` | `/applications` | Save a job as an application |
| `PATCH` | `/applications/{id}` | Update an application's status |
| `DELETE` | `/applications/{id}` | Remove an application |

## What I learned

- **Async SQLAlchemy in production:** `AsyncSession`, `selectinload` and avoiding `MissingGreenlet` errors that only show up at runtime.
- **Claude for structured extraction:** prompts for skills, scoring and review that return parseable data rather than chat.
- **Aggregating 11 inconsistent APIs:** different auth methods, salary fields and rate limits normalised into one schema, with partial failure as the normal case.
- **Deployment across two platforms:** Vercel and Railway, cross-site cookies (`SameSite=None` in production) and CORS between them.
- **XSS-safe auth:** the access token lives in a module-level variable instead of localStorage; the refresh token is in an httpOnly cookie.
- **Accessibility:** combobox keyboard navigation, focus traps, skip links, `aria-live` regions and `role="tab"` patterns.

## License

[MIT](LICENSE)
