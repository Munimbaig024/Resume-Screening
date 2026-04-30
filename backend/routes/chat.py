"""
routes/chat.py — AI chat history endpoints
POST /api/chat        — send a message, get AI response, save to DB
GET  /api/chat        — get chat history for logged-in user
DELETE /api/chat      — clear chat history
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from db.mongo import get_messages
from middleware.auth_guard import jwt_required_cookie
from middleware.input_sanitizer import sanitize_string
from middleware.rate_limiter import limiter, CHAT_LIMIT
from services.ai import _get_client
from config import Config

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

RESUME_ADVISOR_SYSTEM = """You are an expert resume coach and career advisor.
STRICT SCOPE RULES:
1. ONLY discuss resumes, cover letters, LinkedIn profiles, job interviews, and career strategy.
2. REJECT all other topics (coding, math, general info, etc.) with: "I'm sorry, I can only help with resume and career-related questions. How can I assist with your job search?"
3. HARMFUL CONTENT: If the user uses profanity, curses, or requests anything harmful/illegal, respond with: "I cannot assist with that. Please keep our conversation professional and focused on your career goals."
4. NO CODE: Never provide programming code (Python, JS, etc.) even if asked.

Style: Concise, professional, 2-4 sentences."""


@chat_bp.route("", methods=["POST"])
@jwt_required_cookie
@limiter.limit(CHAT_LIMIT)
def send_message():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    content = sanitize_string(data.get("message", ""), 1000)

    if not content:
        return jsonify({"error": "Message cannot be empty"}), 400

    messages_col = get_messages()

    # Save user message
    messages_col.insert_one({
        "userId":    user_id,
        "role":      "user",
        "content":   content,
        "timestamp": datetime.now(timezone.utc),
    })

    # Load recent history (last 10 messages for context)
    history = list(
        messages_col.find(
            {"userId": user_id},
            {"role": 1, "content": 1}
        ).sort("timestamp", -1).limit(10)
    )
    history.reverse()

    # Build messages for Groq
    groq_messages = [{"role": "system", "content": RESUME_ADVISOR_SYSTEM}]
    groq_messages += [{"role": m["role"], "content": m["content"]} for m in history]

    # Call Groq
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=groq_messages,
            temperature=0.7,
            max_tokens=512,
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        reply = "I'm having trouble connecting right now. Please try again in a moment."

    # Save AI reply
    messages_col.insert_one({
        "userId":    user_id,
        "role":      "assistant",
        "content":   reply,
        "timestamp": datetime.now(timezone.utc),
    })

    return jsonify({"reply": reply})


@chat_bp.route("", methods=["GET"])
@jwt_required_cookie
def get_history():
    user_id = get_jwt_identity()
    messages = list(
        get_messages().find(
            {"userId": user_id},
            {"_id": 0, "role": 1, "content": 1, "timestamp": 1}
        ).sort("timestamp", 1).limit(100)
    )
    for m in messages:
        if m.get("timestamp"):
            m["timestamp"] = m["timestamp"].isoformat()
    return jsonify(messages)


@chat_bp.route("", methods=["DELETE"])
@jwt_required_cookie
def clear_history():
    user_id = get_jwt_identity()
    result = get_messages().delete_many({"userId": user_id})
    return jsonify({"deleted": result.deleted_count})
