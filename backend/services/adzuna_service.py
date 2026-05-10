import os
import httpx

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"


async def search_jobs(query: str, results_per_page: int = 20) -> list[dict]:
    """Search UK jobs on Adzuna. Returns list of normalised job dicts."""
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "where": "UK",
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "external_id": str(job["id"]),
            "source": "adzuna",
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", "Unknown"),
            "location": job.get("location", {}).get("display_name", "UK"),
            "salary_min": int(job["salary_min"]) if job.get("salary_min") else None,
            "salary_max": int(job["salary_max"]) if job.get("salary_max") else None,
            "url": job.get("redirect_url", ""),
            "description": job.get("description", ""),
        }
        for job in data.get("results", [])
    ]
