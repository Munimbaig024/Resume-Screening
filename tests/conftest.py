"""
conftest.py — Shared pytest fixtures for the ResumeAI test suite.
The Flask app must be running on localhost:5000 before running tests.
"""
import os
import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"

TEST_USER = {
    "name": "Test User",
    "email": "test_user@resumeai.com",
    "password": "TestPass123!",
    "currentRole": "Software Engineer",
    "experienceYears": 3,
    "linkedInUrl": "https://linkedin.com/in/testuser",
}

TESTS_DIR = os.path.dirname(__file__)
RESUMES_DIR = os.path.join(TESTS_DIR, "resumes")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def resume_munim():
    path = os.path.join(RESUMES_DIR, "resume_munim.pdf")
    if not os.path.exists(path):
        # Fall back to any available PDF in the resumes folder
        for f in os.listdir(RESUMES_DIR):
            if f.endswith(".pdf"):
                return os.path.join(RESUMES_DIR, f)
        pytest.skip("No resume PDF found in tests/resumes/")
    return path


@pytest.fixture(scope="session")
def resume_trillis():
    path = os.path.join(RESUMES_DIR, "resume_trillis.pdf")
    if not os.path.exists(path):
        # Fall back to a different PDF than resume_munim
        pdfs = [f for f in os.listdir(RESUMES_DIR) if f.endswith(".pdf")]
        if len(pdfs) >= 2:
            return os.path.join(RESUMES_DIR, pdfs[1])
        pytest.skip("Need at least 2 resume PDFs in tests/resumes/ for comparison test")
    return path


@pytest.fixture(scope="session")
def resume_strong():
    """Strong resume — high keyword density and achievements."""
    path = os.path.join(RESUMES_DIR, "resume_strong_sarah.pdf")
    if os.path.exists(path):
        return path
    pdfs = sorted(os.listdir(RESUMES_DIR))
    if pdfs:
        return os.path.join(RESUMES_DIR, pdfs[0])
    pytest.skip("No resume PDF found in tests/resumes/")


@pytest.fixture(scope="session")
def resume_weak():
    """Weak resume — minimal content."""
    path = os.path.join(RESUMES_DIR, "resume_weak_jamie.pdf")
    if os.path.exists(path):
        return path
    pdfs = sorted(os.listdir(RESUMES_DIR))
    if len(pdfs) >= 2:
        return os.path.join(RESUMES_DIR, pdfs[-1])
    pytest.skip("Need at least 2 resume PDFs for strong-vs-weak test")


@pytest.fixture(scope="session")
def auth_session(base_url):
    """
    Returns a requests.Session with a valid JWT cookie.
    Registers the test user (ignores 409 if already exists), then logs in.
    """
    session = requests.Session()

    # Register (may already exist — that's fine)
    session.post(f"{base_url}/api/auth/register", json=TEST_USER)

    # Login to get cookies
    resp = session.post(f"{base_url}/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    assert resp.status_code == 200, (
        f"auth_session fixture: login failed ({resp.status_code}): {resp.text}"
    )

    if "csrf_access_token" in session.cookies:
        session.headers.update({"X-CSRF-TOKEN": session.cookies["csrf_access_token"]})

    yield session

    # Cleanup: remove the test user via DB if a delete endpoint exists
    # (No public delete endpoint — cleanup must be done manually or via setup_db.py)
