import re
import httpx
import xml.etree.ElementTree as ET

RSS_URL = "https://weworkremotely.com/remote-jobs.rss"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 10) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(RSS_URL, headers=HEADERS)
            if resp.status_code != 200:
                return []
        except Exception:
            return []

    root = ET.fromstring(resp.content)
    words = [w for w in query.lower().split() if len(w) > 2]

    jobs = []
    for channel in root.findall("channel"):
        for item in channel.findall("item"):
            url = item.findtext("link", "").strip()
            title = item.findtext("title", "").strip()
            if not url or not title:
                continue

            title_lower = title.lower()
            if words and not any(w in title_lower for w in words):
                continue

            guid = item.findtext("guid", url)
            external_id = re.sub(r'[^a-zA-Z0-9_-]', '_', guid)[-64:]
            description = _strip_html(item.findtext("description", ""))

            # WWR title format: "Company: Job Title at Region"
            company = "Unknown"
            if ": " in title:
                parts = title.split(": ", 1)
                company = parts[0].strip()
                title = parts[1].strip()

            jobs.append({
                "external_id": f"wwr_{external_id}",
                "source": "weworkremotely",
                "title": title,
                "company": company,
                "location": "Remote",
                "salary_min": None,
                "salary_max": None,
                "url": url,
                "description": description,
            })

            if len(jobs) >= results_per_page:
                break

    return jobs
