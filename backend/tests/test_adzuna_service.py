import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.adzuna_service import search_jobs


@pytest.mark.asyncio
async def test_search_jobs_returns_list():
    mock_data = {
        "results": [{
            "id": "abc123",
            "title": "Junior Developer",
            "company": {"display_name": "TechCorp"},
            "location": {"display_name": "London"},
            "salary_min": 28000.0,
            "salary_max": 35000.0,
            "redirect_url": "https://adzuna.co.uk/jobs/123",
            "description": "We need a junior developer"
        }]
    }
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_data)
    mock_resp.raise_for_status = MagicMock()

    with patch("services.adzuna_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_jobs("junior developer")

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["source"] == "adzuna"
    assert results[0]["title"] == "Junior Developer"
    assert results[0]["company"] == "TechCorp"
    assert results[0]["external_id"] == "abc123"


@pytest.mark.asyncio
async def test_search_jobs_returns_empty_list_on_no_results():
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value={"results": []})
    mock_resp.raise_for_status = MagicMock()

    with patch("services.adzuna_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_jobs("xyzzy nonexistent job")

    assert results == []
