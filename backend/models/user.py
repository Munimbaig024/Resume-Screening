"""
models/user.py — User document schema helpers
"""
from datetime import datetime, timezone
from bson import ObjectId


def new_user(name: str, email: str, password_hash: bytes, current_role: str = None, experience_years: int = None, linkedin_url: str = None) -> dict:
    return {
        "name":         name,
        "email":        email.lower(),
        "passwordHash": password_hash,
        "role":         "user",             # "user" | "admin"
        "currentRole":  current_role,
        "experienceYears": experience_years,
        "linkedInUrl":  linkedin_url,
        "createdAt":    datetime.now(timezone.utc),
        "lastLoginAt":  None,
        "loginAttempts": 0,
        "lockedUntil":  None,
    }


def serialize_user(user: dict) -> dict:
    """Return safe public fields only (never expose passwordHash)."""
    return {
        "id":        str(user["_id"]),
        "name":      user.get("name"),
        "email":     user.get("email"),
        "role":      user.get("role", "user"),
        "currentRole": user.get("currentRole"),
        "experienceYears": user.get("experienceYears"),
        "linkedInUrl": user.get("linkedInUrl"),
        "createdAt": user.get("createdAt", "").isoformat() if user.get("createdAt") else None,
    }
