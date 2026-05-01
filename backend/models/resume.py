"""Resume and report document helpers."""
from datetime import datetime, timezone


def new_resume(user_id: str, filename: str, parsed_text: str) -> dict:
    return {
        "userId": user_id,
        "fileName": filename,
        "parsedText": parsed_text,
        "uploadedAt": datetime.now(timezone.utc),
    }


def new_report(user_id: str, resume_id: str, industry: str,
               scores: dict, metadata: dict, ai_output: dict) -> dict:
    return {
        "userId": user_id,
        "resumeId": resume_id,
        "industry": industry,
        "scores": scores,
        "metadata": metadata,
        "ai": ai_output,
        "createdAt": datetime.now(timezone.utc),
    }


def serialize_report(report: dict) -> dict:
    return {
        "id": str(report["_id"]),
        "resumeId": str(report.get("resumeId", "")),
        "industry": report.get("industry"),
        "scores": report.get("scores", {}),
        "metadata": report.get("metadata", {}),
        "ai": report.get("ai", {}),
        "createdAt": report.get("createdAt", "").isoformat() if report.get("createdAt") else None,
    }
