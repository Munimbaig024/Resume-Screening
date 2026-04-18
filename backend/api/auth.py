"""
api/auth.py — Register and Login routes with JWT
"""
import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from db.mongo import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not all([name, email, password]):
        return jsonify({"error": "name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    result = db.users.insert_one({
        "name":     name,
        "email":    email,
        "password": hashed,
        "industry": None,
    })

    token = create_access_token(identity=str(result.inserted_id))
    return jsonify({"token": token, "name": name}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = get_db()
    user = db.users.find_one({"email": email})

    if not user or not bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({"token": token, "name": user.get("name", "")}), 200
