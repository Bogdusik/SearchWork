import pytest
from unittest.mock import patch, AsyncMock

MOCK_JOBS = [
    {"external_id": "1", "source": "adzuna", "title": "Junior Dev", "company": "Corp",
     "location": "London", "salary_min": 28000, "salary_max": 35000,
     "url": "https://example.com/1", "description": "Python developer role"},
]

@pytest.mark.asyncio
async def test_search_jobs_returns_sorted_by_match_score(client):
    with patch("routers.jobs.adzuna_service.search_jobs", new_callable=AsyncMock, return_value=MOCK_JOBS), \
         patch("routers.jobs.reed_service.search_jobs", new_callable=AsyncMock, return_value=[]), \
         patch("routers.jobs.get_cv_profile", new_callable=AsyncMock, return_value=["Python", "React"]), \
         patch("routers.jobs.score_job_match", new_callable=AsyncMock, return_value={"score": 85, "matched": ["Python"], "missing": []}):
        resp = await client.get("/jobs?q=junior+developer")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["match_score"] == 85
    assert data[0]["title"] == "Junior Dev"
    assert data[0]["matched_skills"] == ["Python"]

@pytest.mark.asyncio
async def test_search_jobs_requires_query(client):
    resp = await client.get("/jobs")
    assert resp.status_code == 422
