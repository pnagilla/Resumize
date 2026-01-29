"""
NLP Scoring Service - Deterministic, rule-based scoring engine.

No AI calls. Pure Python logic producing explainable scores.

NLP Weights (with JD):
  - 35% Skill Match
  - 25% Keyword Density
  - 25% Experience Alignment
  - 15% Formatting & Structure

NLP Weights (without JD):
  - 25% Skills Present
  - 25% Content Quality
  - 25% Experience Section
  - 25% Formatting & Structure
"""

import re
from typing import Optional


# --- Skill Taxonomy ---
TECH_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby",
    "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "lua", "haskell",
    "objective-c", "dart", "elixir", "clojure", "groovy", "visual basic", "assembly",
    # Frontend
    "react", "angular", "vue", "vue.js", "next.js", "nuxt.js", "svelte", "ember",
    "html", "css", "sass", "less", "tailwind", "bootstrap", "jquery", "webpack",
    "vite", "redux", "graphql", "rest api", "restful",
    # Backend
    "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
    ".net", "asp.net", "rails", "laravel", "gin", "fiber", "nestjs",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "sql server", "mariadb",
    "neo4j", "couchdb", "firestore", "supabase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci", "circleci",
    "cloudformation", "helm", "istio", "prometheus", "grafana", "datadog",
    "new relic", "splunk", "elk",
    # Data & ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "spark", "hadoop", "kafka", "airflow", "dbt",
    "tableau", "power bi", "looker", "snowflake", "databricks", "bigquery",
    "data pipeline", "etl", "data warehouse", "nlp", "computer vision",
    # Tools & Practices
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "agile",
    "scrum", "kanban", "tdd", "microservices", "api design", "oauth",
    "jwt", "ssl/tls", "linux", "bash", "powershell",
    # Mobile
    "react native", "flutter", "ios", "android", "xcode", "android studio",
    # Other
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "salesforce", "hubspot", "sap", "servicenow",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "problem-solving", "analytical",
    "presentation", "time management", "collaboration", "mentoring", "coaching",
    "project management", "stakeholder management", "cross-functional",
    "strategic thinking", "decision making", "negotiation", "conflict resolution",
    "adaptability", "critical thinking", "creativity", "attention to detail",
}

STOP_WORDS = {
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'were', 'being',
    'their', 'there', 'will', 'would', 'could', 'should', 'this', 'that',
    'with', 'from', 'they', 'what', 'about', 'which', 'when', 'make', 'like',
    'into', 'year', 'your', 'some', 'them', 'than', 'then', 'look', 'only',
    'come', 'over', 'such', 'take', 'other', 'also', 'more', 'most', 'just',
    'able', 'must', 'need', 'well', 'each', 'does', 'done', 'much', 'very',
    'both', 'same', 'upon', 'under', 'through', 'between', 'before', 'after',
    'during', 'including', 'within', 'without', 'using', 'based',
}


def extract_skills(text: str) -> dict:
    """
    Extract technical and soft skills from text using keyword matching.
    Returns dict with 'technical' and 'soft' skill lists.
    """
    text_lower = text.lower()
    technical = []
    soft = []

    for skill in TECH_SKILLS:
        # Check for exact match with word boundaries
        # Handle skills with special chars like c++, c#, .net
        escaped = re.escape(skill)
        if re.search(r'(?:^|[\s,;|/(\[])'+ escaped + r'(?:$|[\s,;|/)\]])', text_lower):
            technical.append(skill)

    for skill in SOFT_SKILLS:
        if skill in text_lower:
            soft.append(skill)

    return {"technical": sorted(technical), "soft": sorted(soft)}


def extract_entities(text: str) -> dict:
    """
    Extract job titles, company names, dates, and education entities from text.
    """
    text_lower = text.lower()

    # Job titles
    title_patterns = [
        r'(senior|junior|lead|principal|staff|associate|intern|chief|head|vp|director|manager)?\s*'
        r'(software|data|product|project|marketing|sales|design|devops|cloud|full[\s-]?stack|front[\s-]?end|back[\s-]?end|machine learning|ml|ai|qa|test|security|network|system|database|business|financial|operations|hr|people)?\s*'
        r'(engineer|developer|architect|scientist|analyst|manager|designer|specialist|consultant|administrator|coordinator|lead|officer|strategist|intern)',
    ]
    titles = []
    for pattern in title_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            title = ' '.join(part.strip() for part in match if part.strip())
            if len(title) > 3:
                titles.append(title)

    # Years of experience
    year_patterns = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?', text_lower)
    years = [int(y) for y in year_patterns]

    # Date ranges
    date_ranges = re.findall(
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4})\s*[-–]\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|present|current)',
        text_lower
    )

    # Education
    degrees = []
    degree_patterns = {
        'phd': ['ph\.?d', 'doctorate', 'doctor of'],
        'masters': ['master', 'm\.s\.?', 'm\.a\.?', 'mba', 'm\.sc', 'msc'],
        'bachelors': ['bachelor', 'b\.s\.?', 'b\.a\.?', 'b\.sc', 'bsc', 'b\.eng'],
        'associate': ['associate', 'a\.s\.?', 'a\.a\.?'],
    }
    for level, patterns in degree_patterns.items():
        if any(re.search(p, text_lower) for p in patterns):
            degrees.append(level)

    return {
        "titles": list(set(titles))[:10],
        "years_experience": max(years) if years else 0,
        "date_ranges": date_ranges[:20],
        "degrees": degrees,
    }


def calculate_skill_overlap(resume_skills: list[str], jd_skills: list[str]) -> dict:
    """
    Calculate skill match score between resume and JD extracted skills.
    Uses exact match plus common variations (hyphen/space).
    """
    if not jd_skills:
        return {
            "score": 50,
            "matched": [],
            "missing": [],
            "match_ratio": 0.0,
            "explanation": "No job description skills to match against."
        }

    resume_set = set(s.lower() for s in resume_skills)
    matched = []
    missing = []

    for skill in jd_skills:
        skill_lower = skill.lower()
        variations = {
            skill_lower,
            skill_lower.replace(" ", "-"),
            skill_lower.replace("-", " "),
            skill_lower.replace(".", ""),
            skill_lower.replace(".js", ""),
        }
        if any(v in resume_set for v in variations):
            matched.append(skill)
        else:
            missing.append(skill)

    ratio = len(matched) / len(jd_skills)
    score = int(ratio * 100)

    if ratio >= 0.8:
        explanation = f"Strong skill match. Matched {len(matched)}/{len(jd_skills)} required skills."
    elif ratio >= 0.6:
        explanation = f"Good skill match ({len(matched)}/{len(jd_skills)}). Missing: {', '.join(missing[:3])}."
    elif ratio >= 0.4:
        explanation = f"Partial skill match ({len(matched)}/{len(jd_skills)}). Key gaps: {', '.join(missing[:5])}."
    else:
        explanation = f"Low skill match ({len(matched)}/{len(jd_skills)}). Significant gaps in: {', '.join(missing[:5])}."

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "match_ratio": round(ratio, 2),
        "explanation": explanation
    }


def calculate_keyword_frequency(resume_text: str, jd_text: str) -> dict:
    """
    Calculate keyword density overlap using term frequency comparison.
    Filters out stop words and short words.
    """
    if not jd_text or not jd_text.strip():
        return {
            "score": 50,
            "matched_count": 0,
            "total_keywords": 0,
            "explanation": "No job description provided for keyword matching."
        }

    jd_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', jd_text.lower())) - STOP_WORDS
    resume_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', resume_text.lower())) - STOP_WORDS

    if not jd_words:
        return {
            "score": 50,
            "matched_count": 0,
            "total_keywords": 0,
            "explanation": "No meaningful keywords found in job description."
        }

    matched = jd_words.intersection(resume_words)
    ratio = len(matched) / len(jd_words)
    score = min(int(ratio * 100), 100)

    if ratio >= 0.7:
        explanation = f"Excellent keyword coverage. {len(matched)}/{len(jd_words)} JD keywords found in resume."
    elif ratio >= 0.5:
        explanation = f"Good keyword coverage ({len(matched)}/{len(jd_words)}). Consider adding more JD-specific terms."
    elif ratio >= 0.3:
        explanation = f"Moderate keyword overlap ({len(matched)}/{len(jd_words)}). Resume needs more JD-aligned language."
    else:
        explanation = f"Low keyword overlap ({len(matched)}/{len(jd_words)}). Resume language differs significantly from JD."

    return {
        "score": score,
        "matched_count": len(matched),
        "total_keywords": len(jd_words),
        "explanation": explanation
    }


def calculate_experience_alignment(resume_text: str, jd_text: str) -> dict:
    """
    Calculate experience alignment: years match, title match, industry signals.
    """
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower() if jd_text else ""

    resume_entities = extract_entities(resume_text)
    jd_entities = extract_entities(jd_text) if jd_text else {"titles": [], "years_experience": 0}

    score = 50
    factors = []

    # Years of experience check
    resume_years = resume_entities["years_experience"]
    required_years = jd_entities["years_experience"]

    if required_years > 0:
        if resume_years >= required_years:
            score += 20
            factors.append(f"Meets {required_years}+ years requirement ({resume_years} years found)")
        elif resume_years > 0:
            ratio = resume_years / required_years
            score += int(20 * ratio)
            factors.append(f"Has {resume_years} years, JD asks for {required_years}+")
        else:
            factors.append(f"Years of experience not clearly stated (JD asks for {required_years}+)")
    else:
        if resume_years > 0:
            score += 10
            factors.append(f"{resume_years}+ years of experience detected")

    # Title alignment
    if jd_entities["titles"] and resume_entities["titles"]:
        jd_title_words = set()
        for t in jd_entities["titles"]:
            jd_title_words.update(t.split())
        resume_title_words = set()
        for t in resume_entities["titles"]:
            resume_title_words.update(t.split())

        title_overlap = jd_title_words.intersection(resume_title_words)
        if len(title_overlap) >= 2:
            score += 15
            factors.append("Job title aligns well with resume positions")
        elif len(title_overlap) >= 1:
            score += 8
            factors.append("Partial title alignment with target role")
        else:
            factors.append("Job titles don't closely match the target role")
    elif not resume_entities["titles"]:
        factors.append("No clear job titles detected in resume")

    # Experience section presence
    has_exp_section = any(term in resume_lower for term in
                         ['experience', 'work history', 'employment', 'professional background'])
    if has_exp_section:
        score += 5
    else:
        factors.append("No dedicated experience section found")

    # Quantifiable achievements
    metrics_patterns = [
        r'\d+%', r'\$[\d,]+[KMB]?', r'\d+x',
        r'\d+\+?\s*(users?|customers?|clients?|members?)',
        r'\d+\+?\s*(projects?|products?|features?)',
    ]
    metrics_count = sum(1 for p in metrics_patterns if re.search(p, resume_lower))
    if metrics_count >= 5:
        score += 10
        factors.append(f"Strong use of metrics ({metrics_count} quantifiable achievements)")
    elif metrics_count >= 2:
        score += 5
        factors.append(f"Some metrics found ({metrics_count}). Add more quantifiable results")
    else:
        factors.append("Few/no quantifiable metrics. Add numbers to demonstrate impact")

    score = max(0, min(100, score))
    explanation = ". ".join(factors) if factors else "Experience section evaluated."

    return {
        "score": score,
        "years_match": resume_years >= required_years if required_years > 0 else None,
        "title_match": bool(jd_entities["titles"] and resume_entities["titles"]),
        "resume_years": resume_years,
        "required_years": required_years,
        "explanation": explanation
    }


def calculate_formatting_score(resume_text: str) -> dict:
    """
    Calculate ATS formatting and structure score.
    """
    score = 40
    warnings = []
    positives = []

    resume_lower = resume_text.lower()
    word_count = len(resume_text.split())

    # Length check
    if 400 <= word_count <= 800:
        score += 10
        positives.append("Good resume length")
    elif word_count < 300:
        warnings.append("Resume too short - add more detail")
        score -= 10
    elif word_count > 1200:
        warnings.append("Resume may be too long - aim for 1-2 pages")
        score -= 5

    # Essential sections
    essential = {
        'contact': ['email', 'phone', '@', 'linkedin'],
        'experience': ['experience', 'work history', 'employment'],
        'education': ['education', 'degree', 'university', 'college'],
        'skills': ['skills', 'technologies', 'proficient', 'expertise']
    }
    for section, keywords in essential.items():
        if any(kw in resume_lower for kw in keywords):
            score += 5
        else:
            warnings.append(f"Missing {section.title()} section")
            score -= 5

    # Bullet points (ATS-friendly)
    bullet_count = len(re.findall(r'[•◦\-\*]\s+\w', resume_text))
    if bullet_count >= 8:
        score += 10
        positives.append("Good use of bullet points")
    elif bullet_count >= 4:
        score += 5
    else:
        warnings.append("Add more bullet points for ATS readability")

    # ATS-unfriendly elements
    if resume_text.count('|') > 5:
        warnings.append("Tables detected - may confuse ATS parsers")
        score -= 5
    special_chars = ['→', '←', '★', '●', '◆', '▪', '►']
    if any(c in resume_text for c in special_chars):
        warnings.append("Fancy characters detected - use standard bullets (-, *)")

    # Contact at top
    first_200 = resume_text[:200].lower()
    has_email_top = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', first_200))
    if has_email_top:
        score += 5
        positives.append("Contact info at top")
    else:
        warnings.append("Place contact information at the top")

    # Consistent bullet style
    bullet_types = {
        'bullet': len(re.findall(r'•', resume_text)),
        'dash': len(re.findall(r'^\s*[-]\s', resume_text, re.MULTILINE)),
        'asterisk': len(re.findall(r'^\s*[*]\s', resume_text, re.MULTILINE)),
    }
    used_types = [k for k, v in bullet_types.items() if v > 0]
    if len(used_types) > 1:
        warnings.append("Inconsistent bullet styles - use one type throughout")

    score = max(0, min(100, score))

    if warnings:
        explanation = f"{len(warnings)} formatting issue(s): {warnings[0]}" + (f" and {len(warnings)-1} more" if len(warnings) > 1 else "")
    elif positives:
        explanation = "Good formatting. " + ". ".join(positives[:2])
    else:
        explanation = "Formatting meets basic ATS requirements."

    return {
        "score": score,
        "warnings": warnings,
        "positives": positives,
        "explanation": explanation
    }


def calculate_general_skills_score(resume_text: str) -> dict:
    """Calculate skills score when no JD is provided."""
    skills = extract_skills(resume_text)
    tech_count = len(skills["technical"])
    soft_count = len(skills["soft"])
    score = 30

    if tech_count >= 12:
        score += 35
    elif tech_count >= 8:
        score += 25
    elif tech_count >= 4:
        score += 15
    elif tech_count >= 1:
        score += 5

    if soft_count >= 3:
        score += 15
    elif soft_count >= 1:
        score += 8

    # Skills section present
    if any(term in resume_text.lower() for term in ['skills', 'technologies', 'technical skills']):
        score += 10

    score = min(score, 100)

    explanation = f"Found {tech_count} technical skills and {soft_count} soft skills."
    if tech_count < 5:
        explanation += " Add more technical skills relevant to your target role."

    return {
        "score": score,
        "matched": skills["technical"],
        "missing": [],
        "explanation": explanation
    }


def calculate_content_quality_score(resume_text: str) -> dict:
    """Calculate content quality when no JD is provided."""
    resume_lower = resume_text.lower()
    score = 40

    # Quantifiable achievements
    has_metrics = bool(re.search(r'\d+%|\$[\d,]+|\d+x|\d+\s*(users?|customers?|clients?)', resume_lower))
    if has_metrics:
        score += 20

    # Action verbs
    action_verbs = ['led', 'developed', 'implemented', 'managed', 'created', 'designed',
                    'built', 'optimized', 'increased', 'decreased', 'achieved', 'delivered',
                    'launched', 'streamlined', 'automated', 'spearheaded']
    verb_count = sum(1 for verb in action_verbs if verb in resume_lower)
    if verb_count >= 6:
        score += 20
    elif verb_count >= 3:
        score += 12
    elif verb_count >= 1:
        score += 5

    # Bullet points
    if '•' in resume_text or re.search(r'^\s*[-*]\s', resume_text, re.MULTILINE):
        score += 10

    score = min(score, 100)

    explanation = f"Content quality assessment: {verb_count} strong action verbs found."
    if not has_metrics:
        explanation += " Add quantifiable achievements (%, $, numbers)."

    return {
        "score": score,
        "matched_count": verb_count,
        "total_keywords": len(action_verbs),
        "explanation": explanation
    }


def run_nlp_analysis(resume_text: str, jd_text: str = "") -> dict:
    """
    Run full NLP analysis pipeline. Returns deterministic, explainable scores.
    """
    has_jd = bool(jd_text and jd_text.strip())

    # Extract skills from both documents
    resume_skills = extract_skills(resume_text)
    all_resume_skills = resume_skills["technical"] + resume_skills["soft"]

    if has_jd:
        jd_skills = extract_skills(jd_text)
        all_jd_skills = jd_skills["technical"] + jd_skills["soft"]

        # With JD: targeted matching
        skill_result = calculate_skill_overlap(all_resume_skills, all_jd_skills)
        keyword_result = calculate_keyword_frequency(resume_text, jd_text)
        experience_result = calculate_experience_alignment(resume_text, jd_text)
        formatting_result = calculate_formatting_score(resume_text)

        # Weights: 35% skill, 25% keyword, 25% experience, 15% formatting
        skill_weight = 35
        keyword_weight = 25
        experience_weight = 25
        formatting_weight = 15
    else:
        # Without JD: general quality assessment
        skill_result = calculate_general_skills_score(resume_text)
        keyword_result = calculate_content_quality_score(resume_text)
        experience_result = calculate_experience_alignment(resume_text, "")
        formatting_result = calculate_formatting_score(resume_text)

        # Equal weights for general assessment
        skill_weight = 25
        keyword_weight = 25
        experience_weight = 25
        formatting_weight = 25

    # Calculate weighted scores
    skill_weighted = int(skill_result["score"] * skill_weight / 100)
    keyword_weighted = int(keyword_result["score"] * keyword_weight / 100)
    experience_weighted = int(experience_result["score"] * experience_weight / 100)
    formatting_weighted = int(formatting_result["score"] * formatting_weight / 100)

    nlp_score = skill_weighted + keyword_weighted + experience_weighted + formatting_weighted

    return {
        "nlp_score": max(0, min(100, nlp_score)),
        "breakdown": {
            "skill_match": {
                "score": skill_result["score"],
                "weight": skill_weight,
                "weighted_score": skill_weighted,
                "explanation": skill_result["explanation"],
                "details": {
                    "matched": skill_result.get("matched", []),
                    "missing": skill_result.get("missing", []),
                }
            },
            "keyword_match": {
                "score": keyword_result["score"],
                "weight": keyword_weight,
                "weighted_score": keyword_weighted,
                "explanation": keyword_result["explanation"],
                "details": {
                    "matched_count": keyword_result.get("matched_count", 0),
                    "total_keywords": keyword_result.get("total_keywords", 0),
                }
            },
            "experience_alignment": {
                "score": experience_result["score"],
                "weight": experience_weight,
                "weighted_score": experience_weighted,
                "explanation": experience_result["explanation"],
                "details": {
                    "years_match": experience_result.get("years_match"),
                    "title_match": experience_result.get("title_match", False),
                    "resume_years": experience_result.get("resume_years", 0),
                    "required_years": experience_result.get("required_years", 0),
                }
            },
            "formatting": {
                "score": formatting_result["score"],
                "weight": formatting_weight,
                "weighted_score": formatting_weighted,
                "explanation": formatting_result["explanation"],
                "details": {
                    "warnings": formatting_result.get("warnings", []),
                }
            }
        },
        "extracted_skills": all_resume_skills,
        "extracted_entities": extract_entities(resume_text),
    }
