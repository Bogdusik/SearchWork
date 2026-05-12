import re
import httpx

BASE_URL = "https://www.arbeitnow.com/api/job-board-api"


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 20) -> list[dict]:
    params = {"search": query, "page": 1}
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()

    jobs = []
    for item in resp.json().get("data", []):
        title = item.get("title", "").strip()
        slug = item.get("slug", "")
        url = item.get("url", "")
        if not title or not url:
            continue

        item_location = item.get("location", "")
        is_remote = item.get("remote", False)

        if location != "UK" and location.lower() not in item_location.lower() and not is_remote:
            continue

        description = _strip_html(item.get("description", ""))

        jobs.append({
            "external_id": f"arbeitnow_{slug}",
            "source": "arbeitnow",
            "title": title,
            "company": item.get("company_name", "Unknown"),
            "location": item_location or ("Remote" if is_remote else "Unknown"),
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": description,
        })

        if len(jobs) >= results_per_page:
            break

    return jobs
