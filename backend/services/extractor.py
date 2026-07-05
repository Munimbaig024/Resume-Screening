import re
import io
import pdfplumber
from docx import Document


def extract_text(file_storage) -> str:
    """Extract text from PDF, DOCX, or TXT files."""
    filename = file_storage.filename.lower()
    file_bytes = file_storage.read()
    file_storage.seek(0)

    if filename.endswith(".pdf"):
        return _extract_pdf(file_bytes)
    elif filename.endswith((".docx", ".doc")):
        return _extract_docx(file_bytes)
    elif filename.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def _extract_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())



SECTION_PATTERNS = {
    "summary":    r"\b(summary|profile|objective|about me)\b",
    "experience": r"\b(experience|work history|employment|positions?)\b",
    "education":  r"\b(education|academic|degree|university|college)\b",
    "skills":     r"\b(skills|technical skills|competencies|technologies)\b",
    "projects":   r"\b(projects?|portfolio)\b",
    "contact":    r"\b(contact|email|phone|linkedin|github)\b",
}


def parse_sections(text: str) -> dict:
    """Parse resume sections and return dict with text and presence flags."""
    lines = text.split("\n")
    sections = {k: "" for k in SECTION_PATTERNS}
    current_section = "other"

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        matched = None
        for section, pattern in SECTION_PATTERNS.items():
            if re.search(pattern, line_stripped, re.IGNORECASE) and len(line_stripped) < 60:
                matched = section
                break
        if matched:
            current_section = matched
        elif current_section in sections:
            sections[current_section] += line_stripped + "\n"

    flags = {
        "has_summary":    bool(sections["summary"].strip()),
        "has_experience": bool(sections["experience"].strip()),
        "has_education":  bool(sections["education"].strip()),
        "has_skills":     bool(sections["skills"].strip()),
        "has_projects":   bool(sections["projects"].strip()),
        "has_contact":    bool(sections["contact"].strip()),
        "has_linkedin":   "linkedin" in text.lower(),
        "has_github":     "github" in text.lower(),
    }

    return {**sections, **flags}

def extract_bullets(experience_text: str) -> list[str]:
    """
    Split experience section into individual bullet points / sentences.
    Handles common bullet markers: •, -, *, numbers, or just line breaks.
    """
    bullet_pattern = re.compile(r"^[\s]*[-•*►✓▸]+\s*|^\d+\.\s*", re.MULTILINE)
    lines = experience_text.split("\n")
    bullets = []
    for line in lines:
        cleaned = bullet_pattern.sub("", line).strip()
        if cleaned and len(cleaned) > 20:
            bullets.append(cleaned)
    return bullets



def extract_metadata(text: str, sections: dict) -> dict:
    """Extract high-level metadata to feed the AI prompt."""
    # Name heuristic: first non-empty line that's not an email/URL
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = next((l for l in lines[:5]
                 if not re.search(r"[@/\\.]", l) and len(l.split()) <= 5), "Unknown")

    # Email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.\w+", text)
    email = email_match.group() if email_match else ""

    # Years of experience heuristic: count year mentions (e.g., 2019, 2022)
    years = sorted(set(int(y) for y in re.findall(r"\b(20\d{2}|19\d{2})\b", text)))
    years_exp = (max(years) - min(years)) if len(years) >= 2 else 0

    # Last role: first line of experience section
    exp_lines = [l.strip() for l in sections.get("experience", "").split("\n") if l.strip()]
    last_role = exp_lines[0] if exp_lines else "Unknown"

    # Skills list
    skills_raw = sections.get("skills", "")
    skills = [s.strip() for s in re.split(r"[,|•\n]", skills_raw) if s.strip()][:20]

    # Bullet count and word count
    bullets = extract_bullets(sections.get("experience", ""))

    return {
        "name":        name,
        "email":       email,
        "years_exp":   years_exp,
        "last_role":   last_role,
        "skills":      skills,
        "bullet_count": len(bullets),
        "word_count":  len(text.split()),
    }
