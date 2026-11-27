import os

import httpx

DEFAULT_NTFY_URL = "https://ntfy.sh"


def resolve_ntfy_url() -> str:
    return (os.getenv("NTFY_URL") or "").strip().rstrip("/") or DEFAULT_NTFY_URL


NTFY_URL = resolve_ntfy_url()


class NtfyError(Exception):
    pass


async def send_push(
    topic: str,
    title: str,
    message: str,
    click_url: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
) -> None:
    # JSON publishing instead of headers: job titles often contain non-ASCII ("£", "—"),
    # which HTTP headers cannot carry without extra encoding.
    payload: dict[str, object] = {"topic": topic, "title": title, "message": message}
    if click_url:
        payload["click"] = click_url
    if priority:
        payload["priority"] = priority
    if tags:
        payload["tags"] = tags

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(NTFY_URL, json=payload)
    except httpx.HTTPError as exc:
        raise NtfyError(f"ntfy unreachable: {type(exc).__name__}") from None
    if resp.status_code >= 400:
        raise NtfyError(f"ntfy returned {resp.status_code}")
