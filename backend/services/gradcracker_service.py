import re
import httpx
import defusedxml.ElementTree as ET

# Gradcracker RSS URLs to try in order
RSS_URLS = [
    "https://www.gradcracker.com/jobs/feed/",
    "https://www.gradcracker.com/feed/jobs/",
    "https://www.gradcracker.com/jobs.rss",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-GB,en;q=0.9",
}


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


def _parse_rss(content: bytes, query: str, results_per_page: int) -> list[dict]:
    root = ET.fromstring(content)
    channel = root.find("channel")
    if channel is None:
        return []

    q_lower = query.lower()
    jobs = []
    for item in channel.findall("item"):
        url = item.findtext("link", "").strip()
        title = item.findtext("title", "").strip()
        if not url or not title:
            continue

        # Filter by keyword client-side since RSS may not support query params
        if q_lower and q_lower not in title.lower() and q_lower not in item.findtext("description", "").lower():
            continue

        guid = item.findtext("guid", url)
        external_id = re.sub(r'[^a-zA-Z0-9_-]', '_', guid)[-64:]
        description = _strip_html(item.findtext("description", ""))

        company, location_text = "Unknown", "UK"
        for tag in item:
            tag_name = tag.tag.lower()
            if "company" in tag_name or "employer" in tag_name:
                company = tag.text or company
            if "location" in tag_name or "city" in tag_name:
                location_text = tag.text or location_text

        jobs.append({
            "external_id": f"gradcracker_{external_id}",
            "source": "gradcracker",
            "title": title,
            "company": company,
            "location": location_text,
            "salary_min": None,
            "salary_max": None,
            "url": url,
            "description": description,
        })

        if len(jobs) >= results_per_page:
            break

    return jobs


async def search_jobs(query: str, location: str = "UK", results_per_page: int = 20) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for url in RSS_URLS:
            try:
                resp = await client.get(url, headers=HEADERS)
                if resp.status_code == 200:
                    return _parse_rss(resp.content, query, results_per_page)
            except Exception:
                continue
    return []
