"""Authentication endpoints."""
import bcrypt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies
)

from db.mongo import get_users, get_sessions
from models.user import new_user, serialize_user
from middleware.input_sanitizer import sanitize_string, validate_email, validate_password
from middleware.rate_limiter import limiter, LOGIN_LIMIT, REGISTER_LIMIT

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@auth_bp.route("/register", methods=["POST"])
@limiter.limit(REGISTER_LIMIT)
def register():
    data = request.get_json(silent=True) or {}
    name     = sanitize_string(data.get("name", ""), 100)
    email    = sanitize_string(data.get("email", ""), 200).lower()
    password = data.get("password", "")
    current_role = sanitize_string(data.get("currentRole", ""), 100)
    linkedin_url = sanitize_string(data.get("linkedInUrl", ""), 200)
    
    experience_years = data.get("experienceYears")
    if experience_years is not None:
        try:
            experience_years = int(experience_years)
        except ValueError:
            experience_years = None

    if not all([name, email, password, current_role, experience_years is not None, linkedin_url]):
        return jsonify({"error": "All fields are required"}), 400

    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    ok, msg = validate_password(password)
    if not ok:
        return jsonify({"error": msg}), 400

    users = get_users()
    if users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    result = users.insert_one(new_user(name, email, hashed, current_role, experience_years, linkedin_url))
    user_id = str(result.inserted_id)

    access_token  = create_access_token(identity=user_id, additional_claims={"role": "user"})
    refresh_token = create_refresh_token(identity=user_id)

    resp = make_response(jsonify({"message": "Account created", "name": name}), 201)
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp


@auth_bp.route("/login", methods=["POST"])
@limiter.limit(LOGIN_LIMIT)
def login():
    data  = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", ""), 200).lower()
    password = data.get("password", "")

    users = get_users()
    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # Check lockout
    locked_until = user.get("lockedUntil")
    if locked_until and datetime.now(timezone.utc) < locked_until:
        remaining = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
        return jsonify({"error": f"Account locked. Try again in {remaining} minutes."}), 429

    # Verify password
    if not bcrypt.checkpw(password.encode(), user["passwordHash"]):
        attempts = user.get("loginAttempts", 0) + 1
        update = {"$set": {"loginAttempts": attempts}}
        if attempts >= MAX_ATTEMPTS:
            update["$set"]["lockedUntil"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            update["$set"]["loginAttempts"] = 0
        users.update_one({"email": email}, update)
        return jsonify({"error": "Invalid email or password"}), 401

    # Reset attempts on success
    users.update_one({"email": email}, {
        "$set": {"loginAttempts": 0, "lockedUntil": None, "lastLoginAt": datetime.now(timezone.utc)}
    })

    user_id = str(user["_id"])
    access_token  = create_access_token(identity=user_id, additional_claims={"role": user.get("role", "user")})
    refresh_token = create_refresh_token(identity=user_id)

    resp = make_response(jsonify({"message": "Logged in", "name": user.get("name", ""), "user": serialize_user(user)}))
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True, locations=["cookies"])
def refresh():
    """Issue new access token using refresh token."""
    user_id = get_jwt_identity()
    new_access = create_access_token(identity=user_id)
    resp = make_response(jsonify({"message": "Token refreshed"}))
    set_access_cookies(resp, new_access)
    return resp


@auth_bp.route("/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify({"message": "Logged out"}))
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route("/me", methods=["GET"])
@jwt_required(locations=["cookies"])
def me():
    from bson import ObjectId
    user_id = get_jwt_identity()
    user = get_users().find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(serialize_user(user))
