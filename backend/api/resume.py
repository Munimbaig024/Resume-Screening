"""
api/resume.py — Main resume analysis endpoint
POST /api/resume/analyze
  multipart/form-data:
    - resume:          (file)  PDF, DOCX, or TXT
    - industry:        (str)   e.g. "Software Engineering"
    - job_description: (str)   optional — enables JD-match mode
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from services.extractor import extract_text, parse_sections, extract_bullets, extract_metadata
from services.scorer    import run_all_scores
from services.rag       import jd_similarity_score
from services.ai        import generate_suggestions
from db.mongo           import get_db

resume_bp = Blueprint("resume", __name__, url_prefix="/api/resume")


@resume_bp.route("/analyze", methods=["POST"])
def analyze():
    # JWT is optional — works without login (no MongoDB save)
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass

    # ── Validate inputs ────────────────────────────────────────────────────────
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file     = request.files["resume"]
    industry = request.form.get("industry", "Software Engineering").strip()
    jd_text  = request.form.get("job_description", "").strip() or None

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # ── Step 1: Extract text ───────────────────────────────────────────────────
    try:
        text = extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500

    if len(text.split()) < 50:
        return jsonify({"error": "Resume text too short — check your file"}), 400

    # ── Step 2: Parse sections + bullets ──────────────────────────────────────
    sections = parse_sections(text)
    bullets  = extract_bullets(sections.get("experience", ""))
    metadata = extract_metadata(text, sections)

    # ── Step 3: Run 5 scoring modules ─────────────────────────────────────────
    scores = run_all_scores(text, sections, bullets, industry)

    # ── Step 4: JD similarity (RAG) — if job description provided ─────────────
    jd_result = None
    if jd_text:
        try:
            jd_result = jd_similarity_score(text, jd_text)
            scores["jd_match"] = jd_result["score"]
            scores["jd_gaps"]  = jd_result["gaps"]
        except Exception as e:
            scores["jd_match"] = None
            scores["jd_error"] = str(e)

    # ── Step 5: AI suggestions via Groq ───────────────────────────────────────
    ai_output = generate_suggestions(industry, scores, metadata, jd_text)

    # ── Step 6: Save report to MongoDB (if authenticated) ─────────────────────
    report_id = None
    if user_id:
        try:
            db = get_db()
            report = {
                "userId":     user_id,
                "industry":   industry,
                "filename":   file.filename,
                "scores":     scores,
                "metadata":   metadata,
                "ai":         ai_output,
                "createdAt":  datetime.now(timezone.utc),
            }
            result = db.reports.insert_one(report)
            report_id = str(result.inserted_id)
        except Exception:
            pass  # Don't fail analysis just because DB save failed

    # ── Response ───────────────────────────────────────────────────────────────
    return jsonify({
        "report_id":   report_id,
        "industry":    industry,
        "scores":      scores,
        "metadata":    metadata,
        "jd_analysis": jd_result,
        **ai_output,
    })


@resume_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    """Get all past reports for the logged-in user."""
    user_id = get_jwt_identity()
    db = get_db()
    reports = list(
        db.reports.find(
            {"userId": user_id},
            {"text": 0}  # exclude raw text to keep response small
        ).sort("createdAt", -1).limit(20)
    )
    for r in reports:
        r["_id"] = str(r["_id"])
    return jsonify(reports)
