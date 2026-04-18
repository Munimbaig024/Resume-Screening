"""
middleware/input_sanitizer.py — Input validation and file upload security
"""
import re
import os
from flask import request, jsonify
from config import Config


ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}


def sanitize_string(value: str, max_len: int = 500) -> str:
    """Strip dangerous characters, trim whitespace, enforce max length."""
    if not isinstance(value, str):
        return ""
    # Remove HTML/script tags
    value = re.sub(r"<[^>]+>", "", value)
    # Remove MongoDB operator injection ($, .)
    value = re.sub(r"[\$\x00]", "", value)
    return value.strip()[:max_len]


def validate_email(email: str) -> bool:
    pattern = r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, ""


def validate_file(file) -> tuple[bool, str]:
    """Validate uploaded file: extension, MIME type, size."""
    if not file or not file.filename:
        return False, "No file provided"

    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in Config.ALLOWED_EXTENSIONS:
        return False, f"File type '.{ext}' not allowed. Use PDF, DOCX, or TXT."

    # Check MIME type
    mime = file.content_type or ""
    if mime not in ALLOWED_MIMES and mime != "application/octet-stream":
        return False, f"Invalid MIME type: {mime}"

    # Check file size (read and reset pointer)
    file.seek(0, 2)  # seek to end
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)     # reset
    if size_mb > Config.MAX_UPLOAD_MB:
        return False, f"File too large ({size_mb:.1f}MB). Max {Config.MAX_UPLOAD_MB}MB."

    return True, ""
