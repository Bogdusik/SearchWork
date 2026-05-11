import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.ai_service import extract_cv_skills, score_job_match, generate_cv_review


@pytest.mark.asyncio
async def test_extract_cv_skills_returns_structured_data():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"skills": ["Python", "React"], "job_titles": ["Junior Developer"], "keywords": ["backend", "API"]}')]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        result = await extract_cv_skills("I am a Python developer with React experience")

    assert "skills" in result
    assert "Python" in result["skills"]
    assert "job_titles" in result
    assert "keywords" in result


@pytest.mark.asyncio
async def test_extract_cv_skills_handles_markdown_json():
    """Claude sometimes wraps JSON in markdown code fences — must strip them."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='```json\n{"skills": ["Go"], "job_titles": ["Backend Dev"], "keywords": ["microservices"]}\n```')]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        result = await extract_cv_skills("Go developer")

    assert result["skills"] == ["Go"]


@pytest.mark.asyncio
async def test_score_job_match_returns_integer_0_to_100():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="75")]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        score = await score_job_match(
            cv_skills=["Python", "React"],
            job_description="We need a Python backend developer with React knowledge"
        )

    assert isinstance(score, int)
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_score_job_match_clamps_out_of_range():
    """Score must be clamped to 0-100 even if Claude returns something weird."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="150")]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        score = await score_job_match(cv_skills=["Python"], job_description="Python role")

    assert score == 100


@pytest.mark.asyncio
async def test_generate_cv_review_returns_structured_data():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='''{
        "summary": "Solid foundation.",
        "critical_issues": [{"title": "No email", "detail": "Add plain-text email."}],
        "structural_issues": [{"title": "Generic summary", "detail": "Rewrite it."}],
        "polish_issues": [{"title": "Mixed punctuation", "detail": "Standardise."}],
        "priority_table": [{"priority": 1, "action": "Add email", "impact": "Huge"}]
    }''')]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_cv_review("I am a Python developer.", "Backend Engineer")

    assert result["summary"] == "Solid foundation."
    assert len(result["critical_issues"]) == 1
    assert result["critical_issues"][0]["title"] == "No email"
    assert result["priority_table"][0]["impact"] == "Huge"


@pytest.mark.asyncio
async def test_generate_cv_review_strips_markdown_fences():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='```json\n{"summary": "OK.", "critical_issues": [], "structural_issues": [], "polish_issues": [], "priority_table": []}\n```')]

    with patch("services.ai_service.anthropic_client.messages.create", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_cv_review("CV text", "Full-Stack Developer")

    assert result["summary"] == "OK."
