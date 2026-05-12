import asyncio
from fastapi import APIRouter
from services import adzuna_service, reed_service, jsearch_service, remotive_service, weworkremotely_service, jobicy_service

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/sources")
async def test_sources(q: str = "software developer", location: str = "UK"):
    """Test each job source independently and return counts + sample titles."""

    async def probe(name: str, coro):
        try:
            jobs = await coro
            return {
                "status": "ok",
                "count": len(jobs),
                "samples": [j["title"] for j in jobs[:3]],
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "count": 0, "samples": []}

    adzuna, reed, jsearch, remotive, wwr, jobicy = await asyncio.gather(
        probe("adzuna",         adzuna_service.search_jobs(q, where=location)),
        probe("reed",           reed_service.search_jobs(q, location_name=location)),
        probe("jsearch",        jsearch_service.search_jobs(q, location=location)),
        probe("remotive",       remotive_service.search_jobs(q, location=location)),
        probe("weworkremotely", weworkremotely_service.search_jobs(q, location=location)),
        probe("jobicy",         jobicy_service.search_jobs(q, location=location)),
    )

    return {
        "query": q,
        "location": location,
        "sources": {
            "adzuna": adzuna,
            "reed": reed,
            "jsearch": jsearch,
            "remotive": remotive,
            "weworkremotely": wwr,
            "jobicy": jobicy,
        },
    }
