# ResumeAI Test Suite

## Prerequisites

```bash
pip install pytest requests
```

The Flask app must be running before executing the HTTP-based tests:

```bash
cd backend
venv\Scripts\activate   # Windows
python app.py           # starts on http://localhost:5000
```

---

## Resume Files

Place resume PDFs in `tests/resumes/` before running `test_api.py`:

| Filename | Purpose |
|---|---|
| `resume_munim.pdf` | Primary test resume (should score higher in comparison test) |
| `resume_trillis.pdf` | Comparison resume (should score lower than munim) |

The folder already contains sample files (`resume_strong_sarah.pdf`, `resume_weak_jamie.pdf`, `resume_moderate_marcus.pdf`). If `resume_munim.pdf` / `resume_trillis.pdf` are absent, the fixtures fall back to whatever PDFs are present.

---

## Running Tests

**All tests at once (recommended):**
```bash
python tests/run_tests.py
```

**With pytest directly:**
```bash
pytest tests/ -v
```

**Single file:**
```bash
pytest tests/test_scoring.py -v    # unit tests, no app needed
pytest tests/test_auth.py -v       # auth endpoint tests
pytest tests/test_api.py -v        # analysis + history tests
```

---

## What Each File Covers

| File | Type | Needs app? | Description |
|---|---|---|---|
| `test_scoring.py` | Unit | No | Direct import of scorer functions — range checks, weighted formula, strong vs weak |
| `test_auth.py` | Integration | Yes | Register, login, duplicate email, wrong password, `/api/auth/me` |
| `test_api.py` | Integration | Yes | Analyze (no file, resume-only, with JD, strong vs weak), history auth + array + save |
| `conftest.py` | Fixtures | — | `auth_session`, `base_url`, `resume_munim`, `resume_trillis` shared across files |

---

## Expected Output (Passing Suite)

```
╔══════════════════════════════════════╗
║       ResumeAI Test Suite            ║
╚══════════════════════════════════════╝

Running: pytest tests/test_scoring.py tests/test_auth.py tests/test_api.py -v

collected 21 items

tests/test_scoring.py::test_keyword_score_range PASSED
tests/test_scoring.py::test_achievement_score_range PASSED
tests/test_scoring.py::test_achievement_score_empty_bullets PASSED
tests/test_scoring.py::test_ats_score_range PASSED
tests/test_scoring.py::test_soft_skills_score_range PASSED
tests/test_scoring.py::test_completeness_score_range PASSED
tests/test_scoring.py::test_run_all_scores_keys PASSED
tests/test_scoring.py::test_strong_resume_scores_higher PASSED
tests/test_scoring.py::test_final_score_weighted PASSED
tests/test_auth.py::test_register_success PASSED
tests/test_auth.py::test_register_duplicate PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_auth.py::test_me_authenticated PASSED
tests/test_auth.py::test_me_unauthenticated PASSED
tests/test_api.py::test_analyze_no_file PASSED
tests/test_api.py::test_analyze_with_resume_only PASSED
tests/test_api.py::test_analyze_with_jd PASSED
tests/test_api.py::test_analyze_strong_vs_weak PASSED
tests/test_api.py::test_history_requires_auth PASSED
tests/test_api.py::test_history_returns_array PASSED
tests/test_api.py::test_report_saved PASSED

==================================================
✅  All tests passed.
==================================================
```

---

## Notes

- `test_scoring.py` runs without the app — safe to run any time.
- Each auth test uses a unique email (UUID-based) so repeated runs don't cause 409 conflicts.
- `test_report_saved` verifies the history count grows by exactly 1 after an authenticated analyze call.
- No hardcoded score thresholds — all tests check ranges (0–100) and types, not specific values.
