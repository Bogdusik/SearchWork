import os
import json
import re
import anthropic

anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"

async def extract_cv_skills(cv_text: str) -> dict:
    response = await anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Extract structured data from this CV. Return ONLY valid JSON with these exact keys:
{{
  "skills": ["list of technical skills"],
  "job_titles": ["list of target job titles this person is suited for"],
  "keywords": ["list of key domain keywords"]
}}

CV text:
{cv_text[:8000]}"""
        }]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)

async def score_job_match(cv_skills: list[str], job_description: str) -> int:
    response = await anthropic_client.messages.create(
        model=MODEL,
        max_tokens=16,
        messages=[{
            "role": "user",
            "content": f"""Score how well this job matches this candidate. Return ONLY a single integer 0-100.

Candidate skills: {", ".join(cv_skills)}

Job description (first 1000 chars):
{job_description[:1000]}

Score (0-100):"""
        }]
    )
    raw = response.content[0].text.strip()
    match = re.search(r"\d+", raw)
    score = int(match.group()) if match else 50
    return max(0, min(100, score))

async def generate_cv_review(cv_text: str, target_role: str) -> dict:
    response = await anthropic_client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are a UK graduate recruitment specialist. Review this CV for a candidate targeting: {target_role}.

Return ONLY valid JSON with this exact structure:
{{
  "summary": "2 sentence overall assessment",
  "critical_issues": [
    {{"title": "Issue name", "detail": "Actionable advice"}}
  ],
  "structural_issues": [
    {{"title": "Issue name", "detail": "Actionable advice"}}
  ],
  "polish_issues": [
    {{"title": "Issue name", "detail": "Actionable advice"}}
  ],
  "priority_table": [
    {{"priority": 1, "action": "Action description", "impact": "Huge"}}
  ]
}}

Rules:
- critical_issues: things most likely hurting response rate (contact info, visa/right-to-work, GitHub link, English level phrasing)
- structural_issues: ATS and structure problems (summary, education order, work experience bullets, projects missing metrics)
- polish_issues: punctuation consistency, US/UK spelling, tense, length
- priority_table: 5-8 prioritised actions, impact must be exactly one of: Huge, High, Medium, Low
- Return 3-6 items per section
- Return ONLY JSON, no markdown fences

CV text:
{cv_text[:8000]}"""
        }]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)
