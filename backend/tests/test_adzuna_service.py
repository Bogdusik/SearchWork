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


@pytest.mark.asyncio
async def test_search_jobs_sends_distance_in_km_when_radius_given():
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value={"results": []})
    mock_resp.raise_for_status = MagicMock()

    with patch("services.adzuna_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await search_jobs("developer", where="Dumfries", distance_miles=40)
        params_with_radius = mock_client.get.call_args.kwargs["params"]

        await search_jobs("developer", where="London")
        params_default = mock_client.get.call_args.kwargs["params"]

    assert params_with_radius["distance"] == 64
    assert "distance" not in params_default
