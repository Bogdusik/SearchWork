import os
import json
import re
import anthropic

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


async def extract_cv_skills(cv_text: str) -> dict:
    """Extract skills, job_titles, and keywords from CV text using Claude.

    Returns dict with keys: skills, job_titles, keywords (all lists of strings).
    """
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "Extract structured data from this CV. Return ONLY valid JSON with these exact keys:\n"
                '{"skills": ["list of technical skills"], '
                '"job_titles": ["list of target job titles this person is suited for"], '
                '"keywords": ["list of key domain keywords"]}\n\n'
                f"CV text:\n{cv_text[:8000]}"
            )
        }]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


async def score_job_match(cv_skills: list[str], job_description: str) -> int:
    """Score how well a job description matches the CV skills. Returns 0-100."""
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=16,
        messages=[{
            "role": "user",
            "content": (
                "Score how well this job matches this candidate. Return ONLY a single integer 0-100.\n\n"
                f"Candidate skills: {', '.join(cv_skills)}\n\n"
                f"Job description (first 1000 chars):\n{job_description[:1000]}\n\n"
                "Score (0-100):"
            )
        }]
    )
    raw = response.content[0].text.strip()
    match = re.search(r"\d+", raw)
    score = int(match.group()) if match else 50
    return max(0, min(100, score))
