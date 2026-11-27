import logging

import httpx
import pytest
from unittest.mock import AsyncMock, patch

from routers import jobs as job_search
from services import adzuna_service, reed_service

ADZUNA_ID = "synthetic-adzuna-id-4711"
ADZUNA_KEY = "synthetic-adzuna-key-9f8e7d"
REED_KEY = "synthetic-reed-key-1a2b3c"

OTHER_SOURCES = ["jsearch_service", "remotive_service", "weworkremotely_service", "jobicy_service",
                 "arbeitnow_service", "gradcracker_service", "totaljobs_service", "cwjobs_service",
                 "prospects_service"]


def _mock_http(monkeypatch, module, status: int = 401) -> None:
    real_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": "unauthorised"})

    monkeypatch.setattr(module.httpx, "AsyncClient",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


async def _fetch_with_only(source: str, caplog) -> None:
    keep = {"adzuna": "adzuna_service", "reed": "reed_service"}[source]
    silenced = [n for n in ["adzuna_service", "reed_service", *OTHER_SOURCES] if n != keep]
    patches = [patch.object(getattr(job_search, n), "search_jobs", AsyncMock(return_value=[])) for n in silenced]
    for p in patches:
        p.start()
    try:
        with caplog.at_level(logging.DEBUG):
            await job_search._fetch_for_location("junior developer", "Glasgow")
    finally:
        for p in patches:
            p.stop()


@pytest.mark.asyncio
async def test_adzuna_error_log_does_not_contain_app_key_or_app_id(monkeypatch, caplog):
    monkeypatch.setattr(adzuna_service, "ADZUNA_APP_ID", ADZUNA_ID)
    monkeypatch.setattr(adzuna_service, "ADZUNA_APP_KEY", ADZUNA_KEY)
    _mock_http(monkeypatch, adzuna_service)

    await _fetch_with_only("adzuna", caplog)

    assert "Job service error" in caplog.text
    assert "api.adzuna.com" in caplog.text
    assert ADZUNA_KEY not in caplog.text
    assert ADZUNA_ID not in caplog.text


@pytest.mark.asyncio
async def test_reed_error_log_does_not_contain_api_key(monkeypatch, caplog):
    monkeypatch.setenv("REED_API_KEY", REED_KEY)
    monkeypatch.setattr(reed_service, "REED_API_KEY", REED_KEY)
    _mock_http(monkeypatch, reed_service)

    await _fetch_with_only("reed", caplog)

    assert "Job service error" in caplog.text
    assert REED_KEY not in caplog.text


@pytest.mark.asyncio
async def test_httpx_request_log_does_not_contain_app_key(monkeypatch, caplog):
    import main  # noqa: F401  installs the redaction filter on the httpx logger

    monkeypatch.setattr(adzuna_service, "ADZUNA_APP_ID", ADZUNA_ID)
    monkeypatch.setattr(adzuna_service, "ADZUNA_APP_KEY", ADZUNA_KEY)
    _mock_http(monkeypatch, adzuna_service, status=200)

    with caplog.at_level(logging.INFO, logger="httpx"):
        await adzuna_service.search_jobs("junior developer", where="Glasgow")

    assert "api.adzuna.com" in caplog.text
    assert ADZUNA_KEY not in caplog.text
    assert ADZUNA_ID not in caplog.text


def test_redact_secrets_masks_credential_query_params_and_keeps_the_rest():
    from log_redaction import redact_secrets

    url = ("https://api.adzuna.com/v1/api/jobs/gb/search/1?app_id=abc123&app_key=def456"
           "&what=junior+dev&api_key=x1&token=t2&where=Glasgow")

    redacted = redact_secrets(f"Client error '401 Unauthorized' for url '{url}'")

    for secret in ("abc123", "def456", "x1&", "t2&"):
        assert secret not in redacted
    assert "what=junior+dev" in redacted
    assert "where=Glasgow" in redacted
    assert "app_key=[REDACTED]" in redacted


def test_redact_secrets_masks_configured_key_values_anywhere(monkeypatch):
    from log_redaction import redact_secrets

    monkeypatch.setenv("REED_API_KEY", REED_KEY)

    assert REED_KEY not in redact_secrets(f"auth failed for key {REED_KEY} on reed")


def test_redact_secrets_ignores_short_placeholder_values(monkeypatch):
    from log_redaction import redact_secrets

    monkeypatch.setenv("ADZUNA_APP_ID", "ci")

    assert redact_secrets("cities in scotland") == "cities in scotland"
