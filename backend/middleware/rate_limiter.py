"""
middleware/rate_limiter.py — Flask-Limiter setup
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)

# Per-route limit decorators (import and apply directly to route functions)
LOGIN_LIMIT   = "10 per minute"
REGISTER_LIMIT = "5 per minute"
ANALYZE_LIMIT = "20 per hour"
CHAT_LIMIT    = "30 per minute"
