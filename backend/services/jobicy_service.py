import httpx

BASE_URL = "https://jobicy.com/api/v2/remote-jobs"


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 10) -> list[dict]:
    # Convert query to tag format (first meaningful word)
    tag = query.lower().split()[0] if query else "developer"
    params = {"count": results_per_page, "tag": tag}

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(BASE_URL, params=params)
            if resp.status_code != 200:
                return []
        except Exception:
            return []

    words = [w for w in query.lower().split() if len(w) > 2]
    jobs = []
    for item in resp.json().get("jobs", [])[:results_per_page]:
        job_id = str(item.get("id", ""))
        title = item.get("jobTitle", "").strip()
        url = item.get("url", "")
        if not title or not url:
            continue

        title_lower = title.lower()
        if words and not any(w in title_lower for w in words):
            continue

        jobs.append({
            "external_id": f"jobicy_{job_id}",
            "source": "jobicy",
            "title": title,
            "company": item.get("companyName", "Unknown"),
            "location": item.get("jobGeo") or "Remote",
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": item.get("jobExcerpt", ""),
        })

    return jobs
