import re
import httpx

BASE_URL = "https://remotive.com/api/remote-jobs"


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 10) -> list[dict]:
    params = {"search": query, "limit": results_per_page}
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    words = [w for w in query.lower().split() if len(w) > 2]

    jobs = []
    for item in data.get("jobs", []):
        job_id = str(item.get("id", ""))
        title = item.get("title", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue

        title_lower = title.lower()
        if words and not any(w in title_lower for w in words):
            continue

        description = _strip_html(item.get("description", ""))

        jobs.append({
            "external_id": f"remotive_{job_id}",
            "source": "remotive",
            "title": title,
            "company": item.get("company_name", "Unknown"),
            "location": item.get("candidate_required_location") or "Remote",
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": description,
        })

        if len(jobs) >= results_per_page:
            break

    return jobs
