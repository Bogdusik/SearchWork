import re
import httpx
import defusedxml.ElementTree as ET

INDEED_NS = "https://www.indeed.com/about/"
BASE_URL = "https://www.indeed.com/rss"


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 20) -> list[dict]:
    params = {
        "q": query,
        "l": "United Kingdom" if location == "UK" else location,
        "sort": "date",
        "limit": min(results_per_page, 20),
        "rss": "1",
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SearchWork/1.0)"}
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(BASE_URL, params=params, headers=headers)
        resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    if channel is None:
        return []

    jobs = []
    for item in channel.findall("item"):
        guid = item.findtext("guid", "")
        url = item.findtext("link", "")
        if not url:
            continue

        external_id = guid.split("jk=")[-1].split("&")[0] if "jk=" in guid else guid
        title = item.findtext("title", "").strip()
        company = item.findtext(f"{{{INDEED_NS}}}employer", "Unknown")
        location_text = (
            item.findtext(f"{{{INDEED_NS}}}formattedLocation")
            or item.findtext(f"{{{INDEED_NS}}}city")
            or location
        )
        description = _strip_html(item.findtext("description", ""))

        if not title:
            continue

        jobs.append({
            "external_id": f"indeed_{external_id}",
            "source": "indeed",
            "title": title,
            "company": company,
            "location": location_text,
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": description,
        })

    return jobs
