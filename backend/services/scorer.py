"""Resume scoring modules."""
import re


INDUSTRY_KEYWORDS = {
    "Software Engineering": [
        "python", "javascript", "typescript", "react", "node.js", "sql", "nosql",
        "api", "rest", "graphql", "docker", "kubernetes", "ci/cd", "git",
        "microservices", "agile", "scrum", "aws", "azure", "gcp", "linux",
        "unit testing", "tdd", "system design", "data structures", "algorithms",
        "object-oriented", "devops", "cloud", "scalability", "performance",
        "mongodb", "postgresql", "redis", "flask", "django", "fastapi", "spring",
        "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "etl", "data engineering",
        "rag", "faiss", "llm", "generative ai", "langchain", "elastic search",
    ],
    "Medicine & Health": [
        "patient care", "clinical", "diagnosis", "treatment", "ehr", "emr",
        "icd", "cpt", "hipaa", "surgery", "pharmacology", "anatomy", "pathology",
        "radiology", "nursing", "therapy", "research", "clinical trials",
        "evidence-based", "triage", "protocols", "compliance", "board certified",
        "residency", "fellowship", "telemedicine", "public health", "epidemiology",
        "patient safety", "care coordination", "vital signs", "phlebotomy",
    ],
    "Engineering": [
        "autocad", "solidworks", "cad", "finite element", "simulation",
        "prototyping", "manufacturing", "quality control", "six sigma", "lean",
        "project management", "pmp", "mechanical design", "electrical systems",
        "embedded systems", "matlab", "iso", "safety standards", "testing",
        "technical drawings", "specifications", "rfp", "vendor management",
        "civil engineering", "structural", "hydraulics", "construction",
        "blueprints", "hvac", "plc", "robotics", "scada", "thermodynamics",
    ],
    "Graphic Design": [
        "adobe photoshop", "illustrator", "indesign", "figma", "sketch",
        "ui/ux", "wireframing", "prototyping", "branding", "typography",
        "color theory", "motion graphics", "after effects", "premiere",
        "design systems", "responsive design", "accessibility", "print design",
        "web design", "logo design", "user research", "usability testing",
        "creative direction", "art direction", "visual identity",
        "canva", "procreate", "storyboarding", "vector art", "layout design",
    ],
    "Finance & Business": [
        "financial modeling", "excel", "vba", "sql", "accounting", "gaap", "ifrs",
        "budgeting", "forecasting", "valuation", "dcf", "m&a", "risk management",
        "portfolio", "equity", "fixed income", "derivatives", "compliance",
        "bloomberg", "tableau", "power bi", "strategic planning", "kpi",
        "p&l", "cash flow", "due diligence", "investor relations", "cfa",
        "cpa", "audit", "tax", "banking", "capital markets", "wealth management",
    ],
}

SOFT_SKILLS = [
    "leadership", "collaboration", "communication", "mentored", "mentoring",
    "cross-functional", "stakeholder", "ownership", "initiative",
    "problem-solving", "team", "managed", "coordinated", "organized",
    "negotiated", "presented", "trained", "motivated", "strategic",
    "adaptability", "critical thinking", "time management", "conflict resolution",
]

ACTION_VERBS = [
    "reduced", "improved", "increased", "grew", "cut", "saved", "optimized",
    "launched", "built", "developed", "led", "spearheaded", "achieved",
    "delivered", "scaled", "automated", "streamlined", "implemented",
    "designed", "managed", "created", "coordinated", "executed", "architected",
    "pioneered", "mentored", "transformed", "engineered", "facilitated",
]



def keyword_score(text: str, jd_text: str) -> dict:
    # Build a master list of all known keywords across all domains
    master_keywords = set()
    for kw_list in INDUSTRY_KEYWORDS.values():
        master_keywords.update(kw_list)
    
    # If a job description is provided, filter the master list to only what the JD mentions
    if jd_text and len(jd_text.strip()) > 50:
        jd_lower = jd_text.lower()
        target_keywords = [kw for kw in master_keywords if kw.lower() in jd_lower]
        # If JD has too many keywords, we only require a subset to score high
        # If JD has too few, we fallback
        if len(target_keywords) < 5:
            target_keywords = sorted(list(master_keywords))[:25] 
    else:
        # Fallback if no JD - use Software Engineering as default
        target_keywords = INDUSTRY_KEYWORDS["Software Engineering"]

    text_lower = text.lower()
    found = [kw for kw in target_keywords if kw.lower() in text_lower]
    missing = [kw for kw in target_keywords if kw.lower() not in text_lower]
    
    # Calculate score with a "saturation" point. 
    # If target is large (e.g. 30), matching 20 should already be a very high score.
    target_count = len(target_keywords)
    if target_count == 0:
        score = 100
    else:
        # We use a cap/saturation logic: if you match 80% of keywords in a long list, you get 100.
        # This prevents "score dilution" when a JD is very wordy.
        saturation_point = min(target_count, 15) 
        score = round((len(found) / saturation_point) * 100)
        score = min(score, 100)

    return {
        "score": score,
        "found": found,
        "missing": missing[:10],
    }


QUANTIFIED_PATTERNS = [
    r"\d+%",                            # 30%
    r"\$[\d,.]+[kKmMbB]?",             # $2M, $2.5k, $100,000
    r"\d+x\b",                         # 3x faster
    r"\d+\s?[kKmMbB]\b",               # 50K users, 2 M revenue
    r"\d+ (users|customers|clients|employees|projects|teams|requests|transactions)",
    r"(first|top|best|award|winner|reduced|increased) (by|ranked|within)",
]


def achievement_score(bullets: list[str]) -> int:
    if not bullets:
        return 0

    scores = []
    for bullet in bullets:
        # Check for action verb
        verb_match = any(re.search(r"\b" + re.escape(v) + r"\b", bullet, re.IGNORECASE) for v in ACTION_VERBS)
        # Check for quantifiers
        quant_matches = sum(1 for p in QUANTIFIED_PATTERNS if re.search(p, bullet, re.IGNORECASE))
        
        # A bullet with both a verb and a quantifier is high impact
        if verb_match and quant_matches > 0:
            bullet_score = 100
        elif quant_matches > 1:
            bullet_score = 90
        elif verb_match or quant_matches > 0:
            bullet_score = 60
        else:
            bullet_score = 20 # Basic responsibility bullet
            
        scores.append(bullet_score)

    # We reward resumes with multiple high-impact bullets. 
    # Instead of a pure average, we weight the top 50% of bullets more or use a high-water mark.
    if not scores: return 0
    scores.sort(reverse=True)
    # Average of the better half of bullets + baseline
    top_half = scores[:max(1, len(scores)//2 + 1)]
    avg_score = sum(top_half) / len(top_half)
    
    return round(avg_score)



def ats_score(text: str) -> dict:
    score = 100
    penalties = []
    text_lower = text.lower()

    required_sections = ["experience", "education", "skills"]
    for section in required_sections:
        if section not in text_lower:
            score -= 15
            penalties.append(f"Missing '{section}' section heading")

    # Word count check (ideal: 400–1200 words)
    words = text.split()
    word_count = len(words)
    if word_count < 300:
        score -= 15
        penalties.append(f"Resume too short ({word_count} words, aim for 400+)")
    elif word_count > 1500:
        score -= 10
        penalties.append(f"Resume may be too long ({word_count} words)")

    # Check for common ATS issues (more forgiving)
    if re.search(r"<table|<img", text_lower):
        score -= 5
        penalties.append("HTML/Table tags detected — may confuse some parsers")

    # Check for special characters that trip parsers
    special_chars = len(re.findall(r"[│├┤─┼╔╗╚╝]", text))
    if special_chars > 10:
        score -= 10
        penalties.append("Too many box-drawing characters detected")

    # Contact info check
    if not re.search(r"[\w.+-]+@[\w-]+\.\w+", text):
        score -= 5
        penalties.append("No email address detected")

    return {"score": max(score, 0), "penalties": penalties}



def soft_skills_score(text: str) -> dict:
    text_lower = text.lower()
    found = [s for s in SOFT_SKILLS if s in text_lower]
    # More realistic expectation: matching 5 soft skills is enough for a perfect score
    raw = (len(found) / 5) * 100
    return {
        "score": min(round(raw), 100),
        "found": found,
    }



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



WEIGHTS = {
    "keyword":      0.30,
    "achievement":  0.25,
    "ats":          0.20,
    "soft_skills":  0.15,
    "completeness": 0.10,
}

GRADE_THRESHOLDS = [
    (85, "Excellent"),
    (70, "Good"),
    (55, "Needs Work"),
    (0,  "Poor"),
]


def calculate_final_score(scores: dict) -> dict:
    final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS if k in scores)
    final = round(final)
    grade = next(label for threshold, label in GRADE_THRESHOLDS
                 if final >= threshold)
    return {"score": final, "grade": grade}



def run_all_scores(text: str, sections: dict, bullets: list[str], job_title: str, jd_text: str) -> dict:
    kw     = keyword_score(text, jd_text)
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
