import os
import json
import re
import logging
import anthropic

logger = logging.getLogger(__name__)

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

async def score_job_match(cv_skills: list[str], job_description: str) -> dict:
    response = await anthropic_client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Score how well this job matches this candidate. Return ONLY valid JSON:
{{"score": <integer 0-100>, "matched": [<skills from candidate list relevant to this job>], "missing": [<key skills required by job not in candidate list, max 5>]}}

Candidate skills: {", ".join(cv_skills)}

Job description (first 1000 chars):
{job_description[:1000]}"""
        }]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        result = json.loads(raw)
        score = max(0, min(100, int(result.get("score", 50))))
        return {"score": score, "matched": result.get("matched", []), "missing": result.get("missing", [])}
    except (json.JSONDecodeError, ValueError, TypeError):
        m = re.search(r"\d+", raw)
        return {"score": max(0, min(100, int(m.group()))) if m else 50, "matched": [], "missing": []}

async def generate_cover_letter(cv_text: str, job_title: str, company: str, description: str) -> str:
    response = await anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Write a professional UK-style cover letter for this job application. 3 short paragraphs, approximately 250 words. Use British English. Start with "Dear Hiring Manager," and sign off with "Yours sincerely,".

Job title: {job_title}
Company: {company}
Job description: {description[:1500]}

Candidate background (from CV):
{cv_text[:4000]}

Return ONLY the cover letter text, no extra commentary."""
        }]
    )
    return response.content[0].text.strip()

async def generate_cv_review(cv_text: str, target_role: str) -> dict:
    try:
        response = await anthropic_client.messages.create(
            model=MODEL,
            max_tokens=8096,
            messages=[{
                "role": "user",
                "content": f"""You are a UK graduate recruitment specialist. Review this CV for a candidate targeting: {target_role}.

Return ONLY valid JSON with this exact structure:
{{
  "summary": "2 sentence overall assessment",
  "critical_issues": [
    {{"title": "Issue name", "detail": "Actionable advice in max 20 words"}}
  ],
  "structural_issues": [
    {{"title": "Issue name", "detail": "Actionable advice in max 20 words"}}
  ],
  "polish_issues": [
    {{"title": "Issue name", "detail": "Actionable advice in max 20 words"}}
  ],
  "priority_table": [
    {{"priority": 1, "action": "Action in max 15 words", "impact": "Huge"}}
  ]
}}

Rules:
- critical_issues: things most likely hurting response rate (contact info, visa/right-to-work, GitHub link, English level phrasing)
- structural_issues: ATS and structure problems (summary, education order, work experience bullets, projects missing metrics)
- polish_issues: punctuation consistency, US/UK spelling, tense, length
- priority_table: 5-8 prioritised actions, impact must be exactly one of: Huge, High, Medium, Low
- Return 3-5 items per section (keep it focused)
- Keep all text values SHORT — detail max 20 words, action max 15 words
- Return ONLY JSON, no markdown fences

CV text:
{cv_text[:6000]}"""
            }]
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except anthropic.AuthenticationError as e:
        logger.error("Anthropic API key invalid or missing: %s", e)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Claude response as JSON: %s", e)
        raise
    except Exception as e:
        logger.error("CV review failed: %s", e)
        raise
