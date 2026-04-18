"""
services/scorer.py — All 5 scoring modules + weighted final score
"""
import re

# ── Industry Keyword Lists ─────────────────────────────────────────────────────

INDUSTRY_KEYWORDS = {
    "Software Engineering": [
        "python", "javascript", "typescript", "react", "node.js", "sql", "nosql",
        "api", "rest", "graphql", "docker", "kubernetes", "ci/cd", "git",
        "microservices", "agile", "scrum", "aws", "azure", "gcp", "linux",
        "unit testing", "tdd", "system design", "data structures", "algorithms",
        "object-oriented", "devops", "cloud", "scalability", "performance",
    ],
    "Medicine & Health": [
        "patient care", "clinical", "diagnosis", "treatment", "ehr", "emr",
        "icd", "cpt", "hipaa", "surgery", "pharmacology", "anatomy", "pathology",
        "radiology", "nursing", "therapy", "research", "clinical trials",
        "evidence-based", "triage", "protocols", "compliance", "board certified",
        "residency", "fellowship", "telemedicine", "public health", "epidemiology",
    ],
    "Engineering": [
        "autocad", "solidworks", "cad", "finite element", "simulation",
        "prototyping", "manufacturing", "quality control", "six sigma", "lean",
        "project management", "pmp", "mechanical design", "electrical systems",
        "embedded systems", "matlab", "iso", "safety standards", "testing",
        "technical drawings", "specifications", "rfp", "vendor management",
        "civil engineering", "structural", "hydraulics", "construction",
    ],
    "Graphic Design": [
        "adobe photoshop", "illustrator", "indesign", "figma", "sketch",
        "ui/ux", "wireframing", "prototyping", "branding", "typography",
        "color theory", "motion graphics", "after effects", "premiere",
        "design systems", "responsive design", "accessibility", "print design",
        "web design", "logo design", "user research", "usability testing",
        "creative direction", "art direction", "visual identity",
    ],
    "Finance & Business": [
        "financial modeling", "excel", "vba", "sql", "accounting", "gaap", "ifrs",
        "budgeting", "forecasting", "valuation", "dcf", "m&a", "risk management",
        "portfolio", "equity", "fixed income", "derivatives", "compliance",
        "bloomberg", "tableau", "power bi", "strategic planning", "kpi",
        "p&l", "cash flow", "due diligence", "investor relations", "cfa",
    ],
}

SOFT_SKILLS = [
    "leadership", "collaboration", "communication", "mentored", "mentoring",
    "cross-functional", "stakeholder", "ownership", "initiative",
    "problem-solving", "team", "managed", "coordinated", "organized",
    "negotiated", "presented", "trained", "motivated", "strategic",
]

ACTION_VERBS = [
    "reduced", "improved", "increased", "grew", "cut", "saved", "optimized",
    "launched", "built", "developed", "led", "spearheaded", "achieved",
    "delivered", "scaled", "automated", "streamlined", "implemented",
]


# ── Module 1: Keyword Match (30%) ──────────────────────────────────────────────

def keyword_score(text: str, industry: str) -> dict:
    keywords = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["Software Engineering"])
    text_lower = text.lower()

    found = [kw for kw in keywords if kw.lower() in text_lower]
    missing = [kw for kw in keywords if kw.lower() not in text_lower]
    score = round((len(found) / len(keywords)) * 100)

    return {
        "score": score,
        "found": found,
        "missing": missing[:10],  # top 10 missing
    }


# ── Module 2: Achievement Impact (25%) ────────────────────────────────────────

QUANTIFIED_PATTERNS = [
    r"\d+%",           # 30%
    r"\$[\d,]+",       # $2M
    r"\d+x\b",         # 3x faster
    r"\d+[kKmMbB]\b",  # 50K users, 2M revenue
    r"\d+ (users|customers|clients|employees|projects|teams)",
]


def achievement_score(bullets: list[str]) -> int:
    if not bullets:
        return 0

    scores = []
    for bullet in bullets:
        verb_match = any(re.search(v, bullet, re.IGNORECASE) for v in ACTION_VERBS)
        quant_matches = sum(1 for p in QUANTIFIED_PATTERNS if re.search(p, bullet))
        bullet_score = (25 if verb_match else 0) + min(quant_matches * 25, 75)
        scores.append(min(bullet_score, 100))

    return round(sum(scores) / len(scores))


# ── Module 3: ATS Format (20%) ────────────────────────────────────────────────

def ats_score(text: str) -> dict:
    score = 100
    penalties = []
    text_lower = text.lower()

    required_sections = ["experience", "education", "skills"]
    for section in required_sections:
        if section not in text_lower:
            score -= 15
            penalties.append(f"Missing '{section}' section heading")

    # Word count check (ideal: 300–1200 words)
    word_count = len(text.split())
    if word_count < 300:
        score -= 15
        penalties.append(f"Resume too short ({word_count} words, aim for 400+)")
    elif word_count > 1400:
        score -= 10
        penalties.append(f"Resume may be too long ({word_count} words)")

    # Check for common ATS issues
    if re.search(r"<table|<img|<div", text_lower):
        score -= 10
        penalties.append("HTML tags detected — may confuse ATS")

    # Check for special characters that trip parsers
    special_chars = len(re.findall(r"[│├┤─┼╔╗╚╝]", text))
    if special_chars > 5:
        score -= 10
        penalties.append("Special table/box drawing characters detected")

    # Contact info check
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", text):
        score -= 5
        penalties.append("No email address detected")

    return {"score": max(score, 0), "penalties": penalties}


# ── Module 4: Soft Skills (15%) ───────────────────────────────────────────────

def soft_skills_score(text: str) -> dict:
    text_lower = text.lower()
    found = [s for s in SOFT_SKILLS if s in text_lower]
    # Diminishing returns beyond 8
    raw = (len(found) / 8) * 100
    return {
        "score": min(round(raw), 100),
        "found": found,
    }


# ── Module 5: Completeness (10%) ──────────────────────────────────────────────

def completeness_score(sections: dict) -> int:
    checks = {
        "has_summary":    15,
        "has_experience": 25,
        "has_education":  20,
        "has_skills":     20,
        "has_contact":    10,
        "has_linkedin":    5,
        "has_github":      5,
    }
    return sum(points for check, points in checks.items()
               if sections.get(check, False))


# ── Weighted Final Score ───────────────────────────────────────────────────────

WEIGHTS = {
    "keyword":      0.30,
    "achievement":  0.25,
    "ats":          0.20,
    "soft_skills":  0.15,
    "completeness": 0.10,
}

GRADE_THRESHOLDS = [
    (85, "Excellent 🌟"),
    (70, "Good ✅"),
    (55, "Needs Work ⚠️"),
    (0,  "Poor ❌"),
]


def calculate_final_score(scores: dict) -> dict:
    final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS if k in scores)
    final = round(final)
    grade = next(label for threshold, label in GRADE_THRESHOLDS
                 if final >= threshold)
    return {"score": final, "grade": grade}


# ── Run All Modules ────────────────────────────────────────────────────────────

def run_all_scores(text: str, sections: dict, bullets: list[str], industry: str) -> dict:
    kw     = keyword_score(text, industry)
    ach    = achievement_score(bullets)
    ats    = ats_score(text)
    soft   = soft_skills_score(text)
    comp   = completeness_score(sections)

    raw_scores = {
        "keyword":      kw["score"],
        "achievement":  ach,
        "ats":          ats["score"],
        "soft_skills":  soft["score"],
        "completeness": comp,
    }

    final = calculate_final_score(raw_scores)

    return {
        **raw_scores,
        "final":            final["score"],
        "grade":            final["grade"],
        "missing_keywords": kw["missing"],
        "found_keywords":   kw["found"],
        "ats_penalties":    ats["penalties"],
        "soft_found":       soft["found"],
    }
