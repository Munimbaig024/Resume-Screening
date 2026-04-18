"""
services/ai.py — Groq API integration + structured prompt builder
Sends scored resume data to Groq and gets JSON suggestions back.
"""
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


# ── System Prompt Builder ──────────────────────────────────────────────────────

def build_system_prompt(industry: str, scores: dict, metadata: dict, jd_text: str = None) -> str:
    jd_section = ""
    if jd_text:
        jd_section = f"""
JOB DESCRIPTION PROVIDED:
{jd_text[:1500]}

JD MATCH SCORE: {scores.get('jd_match', 'N/A')}%
JD COVERAGE GAPS: {scores.get('jd_gaps', [])}
"""

    return f"""You are an expert resume coach and hiring consultant with 15 years of experience in {industry}.
You have analyzed a candidate's resume using an automated scoring system. Here is the full data:

AUTOMATED SCORES:
- Keyword Match:       {scores['keyword']}%  — Missing: {scores.get('missing_keywords', [])}
- Achievement Impact:  {scores['achievement']}%
- ATS Compatibility:   {scores['ats']}%      — Issues: {scores.get('ats_penalties', [])}
- Soft Skills:         {scores['soft_skills']}%   — Found: {scores.get('soft_found', [])}
- Completeness:        {scores['completeness']}%
- OVERALL SCORE:       {scores['final']}%    — Grade: {scores['grade']}
{jd_section}
RESUME METADATA:
- Candidate name:          {metadata.get('name', 'Unknown')}
- Estimated experience:    {metadata.get('years_exp', 0)} years
- Current/last role:       {metadata.get('last_role', 'Unknown')}
- Skills listed:           {metadata.get('skills', [])}
- Experience bullet count: {metadata.get('bullet_count', 0)}
- Word count:              {metadata.get('word_count', 0)}

YOUR TASK:
1. Write 4-6 specific, actionable improvement suggestions. Each must:
   - Reference actual resume content or score data above
   - Explain WHY it matters for {industry} hiring managers
   - Give a concrete rewrite example where applicable
2. Identify top 3 missing keywords and explain where to add them naturally
3. Provide one "Quick Win" — the single fastest change to boost the score most
4. Write a brief, honest summary paragraph (2-3 sentences)

IMPORTANT: Respond ONLY with valid JSON in this exact format, no extra text:
{{
  "suggestions": [
    {{"type": "keyword|achievement|ats|completeness|soft_skills", "title": "...", "detail": "...", "example": "...", "priority": "high|medium|low"}}
  ],
  "missing_keywords": [
    {{"keyword": "...", "where_to_add": "..."}}
  ],
  "quick_win": "...",
  "summary_paragraph": "..."
}}"""


# ── Groq API Call ──────────────────────────────────────────────────────────────

def call_groq(prompt: str) -> dict:
    """
    Call Groq API with the scoring prompt.
    Returns parsed JSON dict from the model's response.
    Falls back to a structured error dict if parsing fails.
    """
    client = _get_client()

    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2048,
    )

    raw = completion.choices[0].message.content.strip()

    # Extract JSON block if model wraps it in markdown
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "suggestions": [
                {
                    "type": "general",
                    "title": "Review your resume carefully",
                    "detail": "Our AI encountered an issue generating specific suggestions. "
                              "Please try again or review your scores manually.",
                    "example": "",
                    "priority": "medium",
                }
            ],
            "missing_keywords": [],
            "quick_win": "Focus on the highest-weighted score module with the lowest score.",
            "summary_paragraph": raw[:500] if raw else "AI analysis unavailable.",
        }


# ── Main Entry Point ───────────────────────────────────────────────────────────

def generate_suggestions(industry: str, scores: dict, metadata: dict, jd_text: str = None) -> dict:
    """Build prompt and get AI suggestions from Groq."""
    if not Config.GROQ_API_KEY:
        return {
            "suggestions": [],
            "missing_keywords": [],
            "quick_win": "Add your Groq API key to .env to enable AI suggestions.",
            "summary_paragraph": "AI suggestions disabled — no GROQ_API_KEY set.",
        }

    prompt = build_system_prompt(industry, scores, metadata, jd_text)
    return call_groq(prompt)
