"""
test_auth.py — Integration tests for /api/auth/* endpoints.
Requires the Flask app running on http://127.0.0.1:5000.
"""
import uuid
import requests
import pytest

BASE_URL = "http://127.0.0.1:5000"

# Unique email per test run so repeated runs don't hit 409
UNIQUE_EMAIL = f"testrun_{uuid.uuid4().hex[:8]}@resumeai.com"
VALID_USER = {
    "name": "Pytest Runner",
    "email": UNIQUE_EMAIL,
    "password": "TestPass123!",
    "currentRole": "Software Engineer",
    "experienceYears": 2,
    "linkedInUrl": "https://linkedin.com/in/pytestrunner",
}


@pytest.fixture(scope="module")
def registered_session():
    """Register once, return (session, email) for the whole module."""
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/register", json=VALID_USER)
    assert resp.status_code == 201, (
        f"Setup registration failed ({resp.status_code}): {resp.text}"
    )
    yield session, VALID_USER["email"]


# ── 1. Register success ────────────────────────────────────────────────────────

def test_register_success():
    session = requests.Session()
    unique = {**VALID_USER, "email": f"reg_{uuid.uuid4().hex[:8]}@resumeai.com"}
    resp = session.post(f"{BASE_URL}/api/auth/register", json=unique)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    # JWT cookies must be set
    assert "access_token_cookie" in resp.cookies or "access_token_cookie" in session.cookies, \
        "No access_token_cookie in response cookies"
    data = resp.json()
    assert "message" in data, f"Expected 'message' in response, got {data}"


# ── 2. Register duplicate email ────────────────────────────────────────────────

def test_register_duplicate(registered_session):
    session, email = registered_session
    duplicate = {**VALID_USER, "email": email}
    resp = session.post(f"{BASE_URL}/api/auth/register", json=duplicate)
    assert resp.status_code == 409, (
        f"Expected 409 for duplicate email, got {resp.status_code}: {resp.text}"
    )
    assert "error" in resp.json(), "Expected 'error' key in 409 response"


# ── 3. Login success ───────────────────────────────────────────────────────────

def test_login_success(registered_session):
    _, email = registered_session
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": VALID_USER["password"],
    })
    assert resp.status_code == 200, (
        f"Expected 200 on login, got {resp.status_code}: {resp.text}"
    )
    assert "access_token_cookie" in resp.cookies or "access_token_cookie" in session.cookies, \
        "No JWT cookie set after successful login"


# ── 4. Login wrong password ────────────────────────────────────────────────────

def test_login_wrong_password(registered_session):
    _, email = registered_session
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": "WrongPassword999!",
    })
    assert resp.status_code == 401, (
        f"Expected 401 for wrong password, got {resp.status_code}: {resp.text}"
    )
    assert "error" in resp.json(), "Expected 'error' key in 401 response"


# ── 5. /me authenticated ───────────────────────────────────────────────────────

def test_me_authenticated(registered_session):
    session, email = registered_session
    resp = session.get(f"{BASE_URL}/api/auth/me")
    assert resp.status_code == 200, (
        f"Expected 200 from /api/auth/me, got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    assert "email" in data, f"Expected 'email' in /me response, got {data}"
    assert data["email"] == email, (
        f"Expected email {email}, got {data['email']}"
    )


# ── 6. /me unauthenticated ─────────────────────────────────────────────────────

def test_me_unauthenticated():
    fresh = requests.Session()
    resp = fresh.get(f"{BASE_URL}/api/auth/me")
    assert resp.status_code == 401, (
        f"Expected 401 from /api/auth/me without cookie, got {resp.status_code}: {resp.text}"
    )
