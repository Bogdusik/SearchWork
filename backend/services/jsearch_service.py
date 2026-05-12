import os
import re
import httpx

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
BASE_URL = "https://jsearch.p.rapidapi.com/search"


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


async def search_jobs(query: str, location: str = "United Kingdom", results_per_page: int = 10) -> list[dict]:
    if not RAPIDAPI_KEY:
        return []

    search_query = f"{query} in {location}" if location and location != "UK" else f"{query} in United Kingdom"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": search_query,
        "page": "1",
        "num_pages": "1",
        "country": "gb",
        "date_posted": "month",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(BASE_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for job in data.get("data", [])[:results_per_page]:
        job_id = job.get("job_id", "")
        url = job.get("job_apply_link") or job.get("job_google_link", "")
        if not url:
            continue

        salary_min = job.get("job_min_salary")
        salary_max = job.get("job_max_salary")

        city = job.get("job_city", "")
        country = job.get("job_country", "")
        location_text = ", ".join(filter(None, [city, country])) or "UK"

        description = _strip_html(job.get("job_description", ""))

        jobs.append({
            "external_id": f"jsearch_{job_id}",
            "source": "jsearch",
            "title": job.get("job_title", ""),
            "company": job.get("employer_name", "Unknown"),
            "location": location_text,
            "salary_min": int(salary_min) if salary_min else None,
            "salary_max": int(salary_max) if salary_max else None,
            "url": url,
            "description": description,
        })

    return jobs
