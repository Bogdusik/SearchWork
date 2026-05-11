import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_get_cv_when_no_cv_returns_null(client):
    resp = await client.get("/cv")
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_post_cv_saves_and_returns_profile(client, tmp_path):
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content Python developer React")

    with patch("routers.cv.extract_text_from_pdf", return_value="Python developer with React experience"), \
         patch("routers.cv.extract_cv_skills", new_callable=AsyncMock, return_value={
             "skills": ["Python", "React"],
             "job_titles": ["Junior Developer"],
             "keywords": ["backend"]
         }):
        with open(pdf_path, "rb") as f:
            resp = await client.post("/cv", files={"file": ("cv.pdf", f, "application/pdf")})

    assert resp.status_code == 200
    data = resp.json()
    assert "Python" in data["skills"]
    assert data["job_titles"] == ["Junior Developer"]


@pytest.mark.asyncio
async def test_review_cv_returns_404_when_no_cv(client):
    resp = await client.post("/cv/review", json={"target_role": "Backend Engineer"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_review_cv_returns_review_when_cv_exists(client, tmp_path):
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content Python developer React")

    mock_review = {
        "summary": "Good candidate.",
        "critical_issues": [{"title": "No email", "detail": "Add email."}],
        "structural_issues": [{"title": "Generic summary", "detail": "Rewrite."}],
        "polish_issues": [{"title": "Punctuation", "detail": "Be consistent."}],
        "priority_table": [{"priority": 1, "action": "Add email", "impact": "Huge"}],
    }

    with patch("routers.cv.extract_text_from_pdf", return_value="Python developer with React experience"), \
         patch("routers.cv.extract_cv_skills", new_callable=AsyncMock, return_value={
             "skills": ["Python", "React"],
             "job_titles": ["Junior Developer"],
             "keywords": ["backend"],
         }):
        with open(pdf_path, "rb") as f:
            await client.post("/cv", files={"file": ("cv.pdf", f, "application/pdf")})

    with patch("routers.cv.generate_cv_review", new_callable=AsyncMock, return_value=mock_review):
        resp = await client.post("/cv/review", json={"target_role": "Backend Engineer"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Good candidate."
    assert data["critical_issues"][0]["title"] == "No email"
    assert data["priority_table"][0]["impact"] == "Huge"
