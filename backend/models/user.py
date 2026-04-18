"""
models/user.py — User document schema helpers
"""
from datetime import datetime, timezone
from bson import ObjectId


def new_user(name: str, email: str, password_hash: bytes) -> dict:
    return {
        "name":         name,
        "email":        email.lower(),
        "passwordHash": password_hash,
        "role":         "user",             # "user" | "admin"
        "industry":     None,
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
        "industry":  user.get("industry"),
        "createdAt": user.get("createdAt", "").isoformat() if user.get("createdAt") else None,
    }
