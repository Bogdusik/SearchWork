import os
import base64
import httpx

REED_API_KEY = os.getenv("REED_API_KEY", "")
BASE_URL = "https://www.reed.co.uk/api/1.0/search"


def _auth_header() -> str:
    token = base64.b64encode(f"{REED_API_KEY}:".encode()).decode()
    return f"Basic {token}"


async def search_jobs(query: str, location_name: str = "United Kingdom", results_per_page: int = 20) -> list[dict]:
    params = {
        "keywords": query,
        "locationName": location_name,
        "resultsToTake": results_per_page,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            BASE_URL,
            params=params,
            headers={"Authorization": _auth_header()},
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "external_id": str(job["jobId"]),
            "source": "reed",
            "title": job.get("jobTitle", ""),
            "company": job.get("employerName", "Unknown"),
            "location": job.get("locationName", "UK"),
            "salary_min": int(job["minimumSalary"]) if job.get("minimumSalary") else None,
            "salary_max": int(job["maximumSalary"]) if job.get("maximumSalary") else None,
            "url": job.get("jobUrl", ""),
            "description": job.get("jobDescription", ""),
        }
        for job in data.get("results", [])
    ]
