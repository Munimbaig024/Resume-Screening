"""JWT and role-based access decorators."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt


def jwt_required_cookie(fn):
    """Require a valid JWT access token in HttpOnly cookie."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"])
        except Exception as e:
            return jsonify({"error": "Authentication required", "detail": str(e)}), 401
        return fn(*args, **kwargs)
    return wrapper


def jwt_optional_cookie(fn):
    """Allow request with or without JWT — sets identity to None if missing."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"], optional=True)
        except Exception:
            pass
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Require role=admin in JWT claims."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"])
        except Exception:
            return jsonify({"error": "Authentication required"}), 401
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
