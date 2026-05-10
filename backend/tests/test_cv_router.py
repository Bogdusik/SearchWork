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
