"""
test_scoring.py — Unit tests for backend/services/scorer.py (no HTTP, no app needed).
Import directly from the backend package.
"""
import sys
import os

# Add backend to path so we can import scorer directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.scorer import (
    keyword_score,
    achievement_score,
    ats_score,
    soft_skills_score,
    completeness_score,
    run_all_scores,
    calculate_final_score,
)

# ── Sample data ────────────────────────────────────────────────────────────────

STRONG_RESUME = """
John Smith | john@example.com | linkedin.com/in/johnsmith | github.com/johnsmith

Summary
Experienced Python backend developer with 5 years building scalable REST APIs and microservices.

Experience
Senior Software Engineer — Acme Corp (2020–2024)
- Reduced API latency by 40% by optimizing SQL queries and adding Redis caching
- Led a team of 6 engineers to deliver a Docker/Kubernetes migration
- Built CI/CD pipelines that cut deployment time by 60%
- Scaled platform to 500K users using AWS auto-scaling

Education
BSc Computer Science — State University (2019)

Skills
Python, JavaScript, TypeScript, React, Node.js, SQL, NoSQL, REST, GraphQL, Docker,
Kubernetes, CI/CD, Git, Microservices, Agile, Scrum, AWS, Azure, Linux,
Unit Testing, TDD, System Design, Data Structures, Algorithms, DevOps, Cloud
"""

WEAK_RESUME = """
Jane Doe | janedoe@email.com

Work
Did some things at a company.

Education
Some university.
"""

STRONG_SECTIONS = {
    "has_summary": True,
    "has_experience": True,
    "has_education": True,
    "has_skills": True,
    "has_contact": True,
    "has_linkedin": True,
    "has_github": True,
    "experience": STRONG_RESUME,
}

WEAK_SECTIONS = {
    "has_summary": False,
    "has_experience": False,
    "has_education": False,
    "has_skills": False,
    "has_contact": False,
    "has_linkedin": False,
    "has_github": False,
    "experience": "",
}

STRONG_BULLETS = [
    "Reduced API latency by 40% through SQL optimization",
    "Led team of 6 engineers to deliver $2M project on time",
    "Increased revenue by 25% by launching new feature",
    "Automated deployment pipeline saving 10 hours per week",
    "Grew user base from 10K to 500K customers in 12 months",
]

WEAK_BULLETS = [
    "Did some work",
    "Helped the team",
]


# ── 1. keyword_score range ─────────────────────────────────────────────────────

def test_keyword_score_range():
    result = keyword_score(STRONG_RESUME, None)
    score = result["score"]
    assert 0 <= score <= 100, f"Expected keyword score in [0,100], got {score}"
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"


# ── 2. achievement_score range ─────────────────────────────────────────────────

def test_achievement_score_range():
    score = achievement_score(STRONG_BULLETS)
    assert 0 <= score <= 100, f"Expected achievement score in [0,100], got {score}"
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"


def test_achievement_score_empty_bullets():
    score = achievement_score([])
    assert score == 0, f"Expected 0 for empty bullets, got {score}"


# ── 3. ats_score range ────────────────────────────────────────────────────────

def test_ats_score_range():
    result = ats_score(STRONG_RESUME)
    score = result["score"]
    assert 0 <= score <= 100, f"Expected ATS score in [0,100], got {score}"
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
    assert "penalties" in result, f"Expected 'penalties' key in ats_score result"
    assert isinstance(result["penalties"], list), "penalties should be a list"


# ── 4. soft_skills_score range ────────────────────────────────────────────────

def test_soft_skills_score_range():
    result = soft_skills_score(STRONG_RESUME)
    score = result["score"]
    assert 0 <= score <= 100, f"Expected soft skills score in [0,100], got {score}"
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
    assert "found" in result, "Expected 'found' key in soft_skills_score result"


# ── 5. completeness_score range ───────────────────────────────────────────────

def test_completeness_score_range():
    score = completeness_score(STRONG_SECTIONS)
    assert 0 <= score <= 100, f"Expected completeness score in [0,100], got {score}"
    assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"


# ── 6. run_all_scores — required keys ─────────────────────────────────────────

def test_run_all_scores_keys():
    result = run_all_scores(STRONG_RESUME, STRONG_SECTIONS, STRONG_BULLETS, "Software Engineering", None)
    required = ["keyword", "achievement", "ats", "soft_skills", "completeness", "final"]
    for key in required:
        assert key in result, f"Missing key '{key}' in run_all_scores result: {list(result.keys())}"
        assert isinstance(result[key], (int, float)), (
            f"scores['{key}'] should be numeric, got {type(result[key])}"
        )


# ── 7. Strong resume scores higher than weak ──────────────────────────────────

def test_strong_resume_scores_higher():
    strong = run_all_scores(STRONG_RESUME, STRONG_SECTIONS, STRONG_BULLETS, "Software Engineering", None)
    weak   = run_all_scores(WEAK_RESUME,   WEAK_SECTIONS,   WEAK_BULLETS,   "Software Engineering", None)

    assert strong["final"] > weak["final"], (
        f"Expected strong resume final ({strong['final']}) > weak ({weak['final']})"
    )
    assert strong["completeness"] > weak["completeness"], (
        f"Expected strong completeness ({strong['completeness']}) > weak ({weak['completeness']})"
    )
    assert strong["achievement"] >= weak["achievement"], (
        f"Expected strong achievement ({strong['achievement']}) >= weak ({weak['achievement']})"
    )


# ── 8. Final score weighted formula ───────────────────────────────────────────

def test_final_score_weighted():
    result = run_all_scores(STRONG_RESUME, STRONG_SECTIONS, STRONG_BULLETS, "Software Engineering", None)

    expected = round(
        result["keyword"]      * 0.30 +
        result["achievement"]  * 0.25 +
        result["ats"]          * 0.20 +
        result["soft_skills"]  * 0.15 +
        result["completeness"] * 0.10
    )
    actual = result["final"]

    assert abs(actual - expected) <= 3, (
        f"Final score {actual} deviates >3 from weighted formula result {expected}. "
        f"Scores: keyword={result['keyword']}, achievement={result['achievement']}, "
        f"ats={result['ats']}, soft_skills={result['soft_skills']}, "
        f"completeness={result['completeness']}"
    )
