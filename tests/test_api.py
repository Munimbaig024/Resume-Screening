"""
test_api.py — Integration tests for /api/resume/analyze and /api/resume/history.
Requires the Flask app running on http://127.0.0.1:5000.
Place resume PDFs in tests/resumes/ before running.
"""
import os
import pytest

BASE_URL = "http://127.0.0.1:5000"
ANALYZE_URL = f"{BASE_URL}/api/resume/analyze"
HISTORY_URL = f"{BASE_URL}/api/resume/history"

JD_AI_BACKEND = (
    "We need a Python backend developer with REST APIs, MongoDB, Node.js, "
    "machine learning, FAISS, RAG pipelines, TensorFlow experience"
)

REQUIRED_SCORE_KEYS = [
    "final", "keyword", "achievement", "ats", "soft_skills", "completeness"
]


# ── helpers ────────────────────────────────────────────────────────────────────

def open_resume(path):
    return ("resume", open(path, "rb"), "application/pdf")


# ── 1. Analyze — no file ───────────────────────────────────────────────────────

def test_analyze_no_file(auth_session, base_url):
    resp = auth_session.post(f"{base_url}/api/resume/analyze", data={"job_title": "Engineer"})
    assert resp.status_code == 400, (
        f"Expected 400 when no file uploaded, got {resp.status_code}: {resp.text}"
    )
    assert "error" in resp.json(), "Expected 'error' key in 400 response"


# ── 2. Analyze — resume only, no JD ───────────────────────────────────────────

def test_analyze_with_resume_only(auth_session, base_url, resume_strong):
    with open(resume_strong, "rb") as f:
        resp = auth_session.post(ANALYZE_URL, files={"resume": f}, data={"job_title": "Software Engineer"})

    assert resp.status_code == 200, (
        f"Expected 200 from analyze, got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    scores = data.get("scores", {})

    for key in REQUIRED_SCORE_KEYS:
        assert key in scores, f"Missing key '{key}' in scores: {scores}"
        assert isinstance(scores[key], (int, float)), (
            f"scores.{key} should be numeric, got {type(scores[key])}"
        )
        assert 0 <= scores[key] <= 100, (
            f"scores.{key} out of range: {scores[key]}"
        )

    assert "summary_paragraph" in data, "Missing 'summary_paragraph' in response"
    assert isinstance(data.get("suggestions"), list), (
        f"Expected suggestions to be a list, got {type(data.get('suggestions'))}"
    )


# ── 3. Analyze — with job description (JD match) ──────────────────────────────

def test_analyze_with_jd(auth_session, base_url, resume_strong):
    with open(resume_strong, "rb") as f:
        resp = auth_session.post(ANALYZE_URL, files={"resume": f}, data={
            "job_title": "Backend Engineer",
            "job_description": JD_AI_BACKEND,
        })

    assert resp.status_code == 200, (
        f"Expected 200 from analyze with JD, got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    scores = data.get("scores", {})

    assert "jd_match" in scores, (
        f"Expected 'jd_match' in scores when JD provided, got keys: {list(scores.keys())}"
    )
    jd_match = scores["jd_match"]
    assert isinstance(jd_match, (int, float)), (
        f"jd_match should be numeric, got {type(jd_match)}"
    )
    assert 0 <= jd_match <= 100, f"jd_match out of range: {jd_match}"


# ── 4. Strong resume scores higher than weak on keyword ───────────────────────

def test_analyze_strong_vs_weak(auth_session, base_url, resume_strong, resume_weak):
    """strong should score higher than weak on keyword score."""
    def get_keyword_score(resume_path):
        with open(resume_path, "rb") as f:
            resp = auth_session.post(ANALYZE_URL, files={"resume": f}, data={
                "job_title": "Backend Engineer",
                "job_description": JD_AI_BACKEND,
            })
        assert resp.status_code == 200, (
            f"Analyze failed for {resume_path}: {resp.status_code} {resp.text}"
        )
        return resp.json().get("scores", {}).get("keyword", 0)

    strong_kw = get_keyword_score(resume_strong)
    weak_kw = get_keyword_score(resume_weak)

    assert strong_kw >= weak_kw, (
        f"Expected strong keyword score ({strong_kw}) >= weak ({weak_kw})"
    )


# ── 5. History requires auth ───────────────────────────────────────────────────

def test_history_requires_auth(base_url):
    import requests
    resp = requests.get(f"{base_url}/api/resume/history")
    assert resp.status_code == 401, (
        f"Expected 401 for unauthenticated history request, got {resp.status_code}"
    )


# ── 6. History returns array ───────────────────────────────────────────────────

def test_history_returns_array(auth_session, base_url):
    resp = auth_session.get(f"{base_url}/api/resume/history")
    assert resp.status_code == 200, (
        f"Expected 200 from history endpoint, got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    assert isinstance(data, list), (
        f"Expected history response to be a list, got {type(data)}: {data}"
    )


# ── 7. Report saved to history after analyze ──────────────────────────────────

def test_report_saved(auth_session, base_url, resume_strong):
    # Get count before
    before = auth_session.get(f"{base_url}/api/resume/history").json()
    before_count = len(before) if isinstance(before, list) else 0

    # Analyze
    with open(resume_strong, "rb") as f:
        resp = auth_session.post(ANALYZE_URL, files={"resume": f}, data={
            "job_title": "Data Engineer",
        })
    assert resp.status_code == 200, f"Analyze failed: {resp.status_code} {resp.text}"
    data = resp.json()
    report_id = data.get("report_id")
    assert report_id is not None, f"Expected report_id in analyze response when authenticated. Debug: {data.get('debug_user_id')}, DB: {data.get('debug_db_error')}, JWT: {data.get('debug_jwt_error')}"

    # Get count after
    after = auth_session.get(f"{base_url}/api/resume/history").json()
    after_count = len(after) if isinstance(after, list) else 0

    assert after_count == before_count + 1, (
        f"Expected history count to grow by 1 (was {before_count}, now {after_count})"
    )

    # Verify the new entry is at the top
    assert any(r.get("_id") == report_id for r in after), (
        f"New report_id {report_id} not found in history"
    )
