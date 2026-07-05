"""MongoDB connection and field encryption."""
import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection

try:
    from cryptography.fernet import Fernet
    _fernet = None
    def _get_fernet():
        global _fernet
        if _fernet is None:
            key = os.getenv("ENCRYPTION_KEY", "")
            if key:
                _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return _fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    def _get_fernet(): return None

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        from config import Config
        _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client.get_default_database()
    return _db



def encrypt_field(value: str) -> str:
    """Encrypt a string field for at-rest storage."""
    f = _get_fernet()
    if f and value:
        return f.encrypt(value.encode()).decode()
    return value


def decrypt_field(value: str) -> str:
    """Decrypt an encrypted string field."""
    f = _get_fernet()
    if f and value:
        try:
            return f.decrypt(value.encode()).decode()
        except Exception:
            return value  # return as-is if decryption fails
    return value


def setup_indexes():
    """
    Create all required MongoDB indexes.
    Call once on app startup (idempotent — safe to call multiple times).
    """
    db = get_db()

    # users — unique email, fast lookup
    db.users.create_index([("email", ASCENDING)], unique=True, name="email_unique")

    # resumes — fast lookup per user
    db.resumes.create_index([("userId", ASCENDING)], name="resume_userId")
    db.resumes.create_index([("uploadedAt", DESCENDING)], name="resume_uploadedAt")

    # reports — fast per-user history, sorted by date
    db.reports.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)],
                            name="report_userId_date")

    # sessions — lookup by refreshToken, TTL auto-expire
    db.sessions.create_index([("refreshToken", ASCENDING)], unique=True, name="session_token")
    db.sessions.create_index([("expiresAt", ASCENDING)], expireAfterSeconds=0,
                             name="session_ttl")    # MongoDB TTL index

    # messages — per-user chat history, ordered
    db.messages.create_index([("userId", ASCENDING), ("timestamp", ASCENDING)],
                             name="message_userId_ts")

    print("✅  MongoDB indexes created/verified")


def get_users() -> Collection:    return get_db().users
def get_resumes() -> Collection:  return get_db().resumes
def get_reports() -> Collection:  return get_db().reports
def get_sessions() -> Collection: return get_db().sessions
def get_messages() -> Collection: return get_db().messages
