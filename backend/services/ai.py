"""Groq API integration for AI suggestions."""
import json
import re
from groq import Groq
from config import Config


_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=Config.GROQ_API_KEY)
    return _client


def _stub_response(detail: str = "") -> dict:  
    return {
        "suggestions": [
            {
                "type": "general",
                "title": "AI suggestions temporarily unavailable",
                "detail": "Review your scores above and focus on the lowest-scoring areas first.",
                "example": "",
                "priority": "medium",
            }
        ],
        "missing_keywords": [],
        "quick_win": "Focus on the scoring module with your lowest percentage.",
        "summary_paragraph": detail or "AI analysis unavailable. Use the scores above for guidance.",
    }


def _build_system_message(job_title: str) -> str:
    return f"""You are an expert resume coach and hiring consultant with 15 years of experience hiring for {job_title} roles.
You analyze automated resume scoring data and provide structured, specific, actionable feedback.

Rules:
- Be direct and specific — reference actual scores and data provided
- Every suggestion must have a concrete example or rewrite
- Prioritise changes that will most improve the overall score
- Respond ONLY with valid JSON — no markdown fences, no extra text

Required JSON schema (no other keys allowed):
{{
  "suggestions": [
    {{
      "type": "keyword|achievement|ats|completeness|soft_skills",
      "title": "short action-oriented title",
      "detail": "explanation referencing specific score data",
      "example": "concrete rewrite or before/after example (empty string if not applicable)",
      "priority": "high|medium|low"
    }}
  ],
  "missing_keywords": [
    {{"keyword": "the missing term", "where_to_add": "which section and why"}}
  ],
  "quick_win": "single sentence — the one change that will boost the score most immediately",
  "summary_paragraph": "2-3 honest sentences summarising the resume strengths and biggest gaps"
}}"""


def _build_user_message(job_title: str, scores: dict, metadata: dict, jd_text: str = None) -> str:
    jd_section = ""
    if jd_text:
        jd_section = f"""
JOB DESCRIPTION PROVIDED:
{jd_text[:1500]}

JD MATCH SCORE: {scores.get('jd_match', 'N/A')}%
JD COVERAGE GAPS: {scores.get('jd_gaps', [])}
"""

    return f"""Analyse this resume scoring report and return improvement feedback as JSON.

AUTOMATED SCORES:
- Keyword Match:      {scores['keyword']}%  — Missing: {scores.get('missing_keywords', [])}
- Achievement Impact: {scores['achievement']}%
- ATS Compatibility:  {scores['ats']}%      — Issues: {scores.get('ats_penalties', [])}
- Soft Skills:        {scores['soft_skills']}%   — Found: {scores.get('soft_found', [])}
- Completeness:       {scores['completeness']}%
- OVERALL SCORE:      {scores['final']}%    — Grade: {scores['grade']}
{jd_section}
RESUME METADATA:
- Candidate name:       {metadata.get('name', 'Unknown')}
- Estimated experience: {metadata.get('years_exp', 0)} years
- Current/last role:    {metadata.get('last_role', 'Unknown')}
- Skills listed:        {metadata.get('skills', [])}
- Bullet point count:   {metadata.get('bullet_count', 0)}
- Word count:           {metadata.get('word_count', 0)}

TASKS:
1. Write 4-6 improvement suggestions — each must reference the score data above, explain why it matters for {job_title} hiring managers, and give a concrete rewrite example
2. List the top 3 missing keywords and exactly where to add them
3. Identify the single fastest "quick win" to boost the score
4. Write a brief honest summary paragraph (2-3 sentences)"""


def call_groq(system_msg: str, user_msg: str) -> dict:
    """Call Groq API and return parsed JSON."""
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.4,
            max_tokens=2048,
        )
    except Exception as e:
        return _stub_response(f"Groq API error: {e}")

    raw = completion.choices[0].message.content.strip()

    # Strip markdown code fences if model wraps output
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _stub_response(raw[:500] if raw else "")


def generate_suggestions(job_title: str, scores: dict, metadata: dict, jd_text: str = None) -> dict:
    """Build prompt and get AI suggestions from Groq."""
    print(f"[DEBUG] generate_suggestions: GROQ_API_KEY present = {bool(Config.GROQ_API_KEY)}")
    print(f"[DEBUG] GROQ_API_KEY value (first 20 chars): {Config.GROQ_API_KEY[:20] if Config.GROQ_API_KEY else 'EMPTY'}")
    
    if not Config.GROQ_API_KEY:
        print("[DEBUG] GROQ_API_KEY is empty! Returning stub response.")
        return {
            "suggestions": [],
            "missing_keywords": [],
            "quick_win": "Add your Groq API key to .env to enable AI suggestions.",
            "summary_paragraph": "AI suggestions disabled — no GROQ_API_KEY set.",
        }

    system_msg = _build_system_message(job_title)
    user_msg   = _build_user_message(job_title, scores, metadata, jd_text)
    result = call_groq(system_msg, user_msg)
    print(f"[DEBUG] Groq suggestions result: {result}")
    return result
