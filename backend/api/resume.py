"""
api/resume.py — Main resume analysis endpoint
POST /api/resume/analyze
  multipart/form-data:
    - resume:          (file)  PDF, DOCX, or TXT
    - job_title:       (str)   e.g. "Senior Frontend Engineer"
    - job_description: (str)   Full text of job description
"""
from datetime import datetime, timezone
import urllib.parse
import urllib.request
import json as json_mod
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from bson import ObjectId
from services.extractor import extract_text, parse_sections, extract_bullets, extract_metadata
from services.scorer    import run_all_scores
from services.rag       import jd_similarity_score
from services.ai        import generate_suggestions, call_groq
from middleware.auth_guard import jwt_required_cookie
from db.mongo           import get_db

resume_bp = Blueprint("resume", __name__, url_prefix="/api/resume")


@resume_bp.route("/analyze", methods=["POST"])
def analyze():
    # JWT is optional — works without login (no MongoDB save)
    jwt_error = None
    user_id = None
    try:
        verify_jwt_in_request(optional=True, locations=["cookies"])
        user_id = get_jwt_identity()
    except Exception as e:
        jwt_error = str(e)
        pass

    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file     = request.files["resume"]
    job_title = request.form.get("job_title", "Custom Role").strip()
    jd_text  = request.form.get("job_description", "").strip() or None

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400


    try:
        text = extract_text(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500

    if len(text.split()) < 50:
        return jsonify({"error": "Resume text too short — check your file"}), 400

    sections = parse_sections(text)
    bullets  = extract_bullets(sections.get("experience", ""))
    metadata = extract_metadata(text, sections)

    scores = run_all_scores(text, sections, bullets, job_title, jd_text)

    jd_result = None
    if jd_text:
        try:
            jd_result = jd_similarity_score(text, jd_text)
            scores["jd_match"] = jd_result["score"]
            scores["jd_gaps"]  = jd_result["gaps"]
        except Exception as e:
            scores["jd_match"] = None
            scores["jd_error"] = str(e)

    try:
        ai_output = generate_suggestions(job_title, scores, metadata, jd_text)
    except Exception:
        ai_output = {
            "suggestions": [],
            "missing_keywords": [],
            "quick_win": "",
            "summary_paragraph": "AI suggestions are temporarily unavailable.",
        }

    report_id = None
    db_error = None
    if user_id:
        try:
            db = get_db()
            report = {
                "userId":     user_id,
                "jobTitle":   job_title,
                "jdText":     jd_text,
                "filename":   file.filename,
                "scores":     scores,
                "metadata":   metadata,
                "ai":         ai_output,
                "createdAt":  datetime.now(timezone.utc),
            }
            result = db.reports.insert_one(report)
            report_id = str(result.inserted_id)
        except Exception as e:
            print(f"DB Insert failed: {e}")
            db_error = str(e)

    return jsonify({
        "report_id":   report_id,
        "debug_user_id": user_id if 'user_id' in locals() else None,
        "debug_jwt_error": jwt_error,
        "debug_db_error": db_error,
        "job_title":   job_title,
        "scores":      scores,
        "metadata":    metadata,
        "jd_analysis": jd_result,
        **ai_output,
    })


@resume_bp.route("/history", methods=["GET"])
@jwt_required(locations=["cookies"])
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


@resume_bp.route("/cover-letter", methods=["POST"])
@jwt_required_cookie
def cover_letter():
    """Generate a tailored cover letter from a saved report."""
    user_id = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    report_id = body.get("report_id", "").strip()
    tone      = body.get("tone", "professional").strip().lower()

    if tone not in ("professional", "casual", "enthusiastic"):
        tone = "professional"

    if not report_id:
        return jsonify({"error": "report_id is required"}), 400

    try:
        oid = ObjectId(report_id)
    except Exception:
        return jsonify({"error": "Invalid report_id"}), 400

    db = get_db()
    report = db.reports.find_one({"_id": oid, "userId": user_id})
    if not report:
        return jsonify({"error": "Report not found"}), 404

    ai_data   = report.get("ai", {})
    scores    = report.get("scores", {})
    metadata  = report.get("metadata", {})
    
    job_title = report.get("jobTitle", "the role")
    jd_text   = report.get("jdText", "")
    name      = metadata.get("name", "the candidate")
    last_role = metadata.get("last_role", "a previous position")
    years_exp = metadata.get("years_exp", 0)
    
    # Extract specific AI insights
    summary_paragraph = ai_data.get("summary_paragraph", "")
    quick_win         = ai_data.get("quick_win", "")
    found_keywords    = ", ".join(scores.get("found_keywords", []))
    missing_keywords  = ", ".join(scores.get("missing_keywords", []))
    
    # Extract high priority suggestions details
    suggestions = ai_data.get("suggestions", [])
    high_priority_details = [
        s.get("detail", "") for s in suggestions 
        if s.get("priority", "").lower() == "high"
    ]
    high_priority_text = "\n".join(high_priority_details)

    jd_section = ""
    if jd_text:
        jd_section = f"JOB DESCRIPTION:\n{jd_text}\n\nMirror the employer's language naturally."
    else:
        jd_section = f"No JD available — write for a general {job_title} role."

    system_msg = """You are a professional cover letter writer. 
Write concise, specific, achievement-driven cover letters.
Rules:
- NEVER use: "esteemed", "passionate", "excited to apply", "truly", "delve", 
  "I am writing to apply", "perfect fit", "dream job", or any similar filler phrases
- NEVER open with "I" — start with a specific achievement or bold statement
- Every claim must reference specific numbers, tools, or outcomes from the resume
- 3 paragraphs only: (1) hook with strongest achievement, (2) skill match to JD, (3) short CTA
- Tone must match: {tone}
- Maximum 250 words
- Sound like a real human wrote this, not an AI""".replace("{tone}", tone)

    user_msg = f"""Write a cover letter for this candidate:

CANDIDATE: {name}
APPLYING FOR: {job_title}
EXPERIENCE: {years_exp} years, most recent role: {last_role}

THEIR STRONGEST ACHIEVEMENTS (use these specifically):
{summary_paragraph}
{high_priority_text}

SKILLS THAT MATCH THIS JOB:
{found_keywords}

GAPS TO ADDRESS NATURALLY IN THE LETTER:
{missing_keywords}

QUICK WIN INSIGHT:
{quick_win}

{jd_section}

Write the cover letter now. Start strong. Be specific. No filler."""

    try:
        from groq import Groq
        from config import Config
        if not Config.GROQ_API_KEY:
            raise ValueError("No GROQ_API_KEY")
        client = Groq(api_key=Config.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        letter = completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

    return jsonify({
        "cover_letter":    letter,
        "job_title":       job_title,
        "candidate_name":  name,
    })


@resume_bp.route("/cold-email", methods=["POST"])
@jwt_required_cookie
def cold_email():
    """Generate a punchy cold email from a saved report."""
    user_id = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    report_id = body.get("report_id", "").strip()
    tone      = body.get("tone", "professional").strip().lower()

    if tone not in ("professional", "casual", "enthusiastic"):
        tone = "professional"

    if not report_id:
        return jsonify({"error": "report_id is required"}), 400

    try:
        oid = ObjectId(report_id)
    except Exception:
        return jsonify({"error": "Invalid report_id"}), 400

    db = get_db()
    report = db.reports.find_one({"_id": oid, "userId": user_id})
    if not report:
        return jsonify({"error": "Report not found"}), 404

    ai_data   = report.get("ai", {})
    scores    = report.get("scores", {})
    metadata  = report.get("metadata", {})
    
    job_title = report.get("jobTitle", "the role")
    jd_text   = report.get("jdText", "")
    name      = metadata.get("name", "the candidate")
    last_role = metadata.get("last_role", "a previous position")
    years_exp = metadata.get("years_exp", 0)
    
    summary_paragraph = ai_data.get("summary_paragraph", "")
    quick_win         = ai_data.get("quick_win", "")
    found_keywords    = scores.get("found_keywords", [])[:8]
    
    jd_section = ""
    if jd_text:
        jd_section = f"JOB DESCRIPTION:\n{jd_text}\n\nMirror the employer's language naturally."
    else:
        jd_section = f"No JD available — write for a general {job_title} role."

    system_msg = """You are an expert at writing cold outreach emails for job seekers.
Write short, punchy cold emails that get responses.
Rules:
- Maximum 120 words total (subject line not counted)
- Always start with a professional greeting (e.g. "Hi [Name]," or "Hi there,")
- NEVER use: "I hope this email finds you well", "I am reaching out", 
  "I wanted to", "I am passionate", "perfect fit", or any filler phrases
- Subject line must include the job title and your name or a specific value (e.g. "Application for {job_title} - {name}" or "{job_title} Outreach - {name}")
- Open with one specific achievement or bold value statement
- One sentence on skill match to the role
- Clear single CTA: ask for a 15-minute call, not a full interview
- End with name and one-line contact (email + LinkedIn)
- Sound human, direct, confident"""

    user_msg = f"""Write a cold email for this candidate reaching out about a {job_title} role:

Name: {name}
Experience: {years_exp} years, last role: {last_role}  
Top skills matching this role: {', '.join(found_keywords)}
Strongest achievement: extract the best quantified result from {summary_paragraph}
Quick win they offer: {quick_win}
Tone: {tone}

{jd_section}

Return in this exact format:
SUBJECT: [subject line here]

[Greeting],

[email body here]""".replace("{job_title}", job_title).replace("{name}", name)

    try:
        from groq import Groq
        from config import Config
        if not Config.GROQ_API_KEY:
            raise ValueError("No GROQ_API_KEY")
        client = Groq(api_key=Config.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.8,
            max_tokens=300,
        )
        content = completion.choices[0].message.content.strip()
        
        # Parse subject and body
        subject = ""
        body_text = content
        if "SUBJECT:" in content:
            # Look for the first blank line after SUBJECT:
            lines = content.split("\n")
            subject = lines[0].replace("SUBJECT:", "").strip()
            body_text = "\n".join(lines[1:]).strip()
                
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

    return jsonify({
        "subject":         subject,
        "body":            body_text,
        "job_title":       job_title,
        "candidate_name":  name,
    })


@resume_bp.route("/search-jobs", methods=["GET"])
@jwt_required_cookie
def search_jobs():
    """Search Adzuna for jobs matching the resume's keywords and job title."""
    from config import Config
    user_id = get_jwt_identity()
    report_id = request.args.get("report_id", "").strip()

    if not report_id:
        return jsonify({"error": "report_id is required"}), 400

    try:
        oid = ObjectId(report_id)
    except Exception:
        return jsonify({"error": "Invalid report_id"}), 400

    db = get_db()
    report = db.reports.find_one({"_id": oid, "userId": user_id})
    if not report:
        return jsonify({"error": "Report not found"}), 404

    scores   = report.get("scores", {})
    metadata = report.get("metadata", {})

    job_title      = report.get("jobTitle", "")
    found_keywords = scores.get("found_keywords", [])
    last_role      = metadata.get("last_role", "")

    if job_title and job_title != "Custom Role":
        query = job_title
    elif found_keywords:
        query = " ".join(found_keywords[:3])
    elif last_role:
        query = last_role
    else:
        query = "Software Engineer"

    if not Config.ADZUNA_APP_ID or not Config.ADZUNA_APP_KEY:
        return jsonify({"jobs": [], "error": "Job search unavailable"}), 503

    VALID_COUNTRIES = {"us", "gb", "au", "ca", "de", "fr", "sg", "in", "nl", "nz", "za"}
    country = request.args.get("country", "us").strip().lower()
    if country == "pk":
        country = "gb"  # Adzuna has no pk endpoint; gb has the most international remote jobs
    if country not in VALID_COUNTRIES:
        country = "us"

    max_days = request.args.get("max_days_old", "0").strip()
    try:
        max_days = int(max_days)
    except:
        max_days = 0

    adzuna_params = {
        "app_id":          Config.ADZUNA_APP_ID,
        "app_key":         Config.ADZUNA_APP_KEY,
        "results_per_page": 12,  # increased for better selection
        "what":            query,
        "content-type":    "application/json",
    }
    if max_days > 0:
        adzuna_params["max_days_old"] = max_days

    params = urllib.parse.urlencode(adzuna_params)
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{params}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json_mod.loads(resp.read().decode())
    except Exception as e:
        print(f"Adzuna API Error: {str(e)} | URL: {url}")
        return jsonify({"jobs": [], "error": f"Job search unavailable: {str(e)}"}), 200

    results = raw.get("results", [])
    jobs = []
    for r in results:
        loc = r.get("location", {})
        loc_str = ", ".join(filter(None, [
            loc.get("display_name", ""),
        ])) or "Remote"
        jobs.append({
            "title":       r.get("title", ""),
            "company":     r.get("company", {}).get("display_name", ""),
            "location":    loc_str,
            "salary_min":  r.get("salary_min", 0) or 0,
            "salary_max":  r.get("salary_max", 0) or 0,
            "description": (r.get("description", "") or "")[:150],
            "url":         r.get("redirect_url", ""),
            "created":     r.get("created", ""),
        })

    return jsonify({
        "jobs":          jobs,
        "query_used":    query,
        "country_used":  country,
        "total_results": raw.get("count", len(jobs)),
    })
