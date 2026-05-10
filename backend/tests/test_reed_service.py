import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.reed_service import search_jobs


@pytest.mark.asyncio
async def test_search_jobs_returns_list():
    mock_data = {
        "results": [{
            "jobId": 999,
            "jobTitle": "Graduate Engineer",
            "employerName": "HSBC",
            "locationName": "Edinburgh",
            "minimumSalary": 30000.0,
            "maximumSalary": 38000.0,
            "jobUrl": "https://reed.co.uk/jobs/999",
            "jobDescription": "Graduate software engineer role"
        }]
    }
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_data)
    mock_resp.raise_for_status = MagicMock()

    with patch("services.reed_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_jobs("graduate engineer")

    assert isinstance(results, list)
    assert results[0]["source"] == "reed"
    assert results[0]["title"] == "Graduate Engineer"
    assert results[0]["external_id"] == "999"


@pytest.mark.asyncio
async def test_search_jobs_returns_empty_list_on_no_results():
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value={"results": []})
    mock_resp.raise_for_status = MagicMock()

    with patch("services.reed_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        results = await search_jobs("xyzzy")

    assert results == []
