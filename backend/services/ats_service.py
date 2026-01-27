"""
ATS Scoring Service - Deterministic scoring logic that mirrors real ATS systems.

Final ATS Score Breakdown:
  - 40% Skill Match
  - 30% Keyword Match
  - 20% Experience Match
  - 10% Formatting & Structure
"""

import re
from typing import Tuple


def calculate_skill_match(resume_text: str, jd_skills: list[str]) -> Tuple[int, list[str], list[str]]:
    """
    Calculate skill match score (40% weight).
    Returns: (score 0-100, matched_skills, missing_skills)
    """
    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for skill in jd_skills:
        skill_lower = skill.lower()
        # Check for exact match or common variations
        variations = [skill_lower, skill_lower.replace(" ", "-"), skill_lower.replace("-", " ")]
        if any(var in resume_lower for var in variations):
            matched.append(skill)
        else:
            missing.append(skill)

    if not jd_skills:
        return 50, [], []  # Neutral score if no skills specified

    score = int((len(matched) / len(jd_skills)) * 100)
    return score, matched, missing


def calculate_keyword_match(resume_text: str, job_description: str) -> Tuple[int, int, int]:
    """
    Calculate keyword overlap score (30% weight).
    Returns: (score 0-100, matched_count, total_keywords)
    """
    # Extract meaningful keywords from JD (nouns, technical terms)
    jd_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', resume_text.lower()))

    # Filter out common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
                  'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'were', 'being',
                  'their', 'there', 'will', 'would', 'could', 'should', 'this', 'that',
                  'with', 'from', 'they', 'what', 'about', 'which', 'when', 'make', 'like',
                  'into', 'year', 'your', 'some', 'them', 'than', 'then', 'look', 'only',
                  'come', 'over', 'such', 'take', 'other', 'experience', 'work', 'working'}

    jd_keywords = jd_words - stop_words
    matched = jd_keywords.intersection(resume_words)

    if not jd_keywords:
        return 50, 0, 0

    score = int((len(matched) / len(jd_keywords)) * 100)
    score = min(score, 100)  # Cap at 100
    return score, len(matched), len(jd_keywords)


def calculate_experience_match(resume_text: str, job_description: str) -> Tuple[int, str]:
    """
    Calculate experience relevance score (20% weight).
    Returns: (score 0-100, experience_note)
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # Extract years mentioned in resume
    resume_years = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', resume_lower)
    jd_years = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', jd_lower)

    max_resume_years = max([int(y) for y in resume_years], default=0)
    required_years = min([int(y) for y in jd_years], default=0) if jd_years else 0

    # Check for experience-related sections
    has_experience_section = any(term in resume_lower for term in
                                  ['experience', 'work history', 'employment', 'professional background'])

    # Calculate score
    score = 50  # Base score
    note = ""

    if required_years > 0:
        if max_resume_years >= required_years:
            score = 100
            note = f"Meets {required_years}+ years requirement"
        elif max_resume_years > 0:
            score = int((max_resume_years / required_years) * 100)
            note = f"Has {max_resume_years} years, JD asks for {required_years}+"
        else:
            score = 30
            note = f"Years not clearly stated, JD asks for {required_years}+"
    else:
        score = 70 if has_experience_section else 50
        note = "Experience section found" if has_experience_section else "No specific years required"

    return min(score, 100), note


def calculate_formatting_score(resume_text: str) -> Tuple[int, list[str]]:
    """
    Calculate formatting & structure score (10% weight).
    Returns: (score 0-100, warnings)
    """
    warnings = []
    score = 100

    resume_lower = resume_text.lower()

    # Check for essential sections
    essential_sections = {
        'contact': ['email', 'phone', '@', 'linkedin'],
        'experience': ['experience', 'work history', 'employment'],
        'education': ['education', 'degree', 'university', 'college'],
        'skills': ['skills', 'technologies', 'proficient', 'expertise']
    }

    for section, keywords in essential_sections.items():
        if not any(kw in resume_lower for kw in keywords):
            warnings.append(f"Missing {section.title()} section")
            score -= 15

    # Check for potential ATS issues
    if len(resume_text) < 300:
        warnings.append("Resume appears too short")
        score -= 20

    if len(resume_text) > 10000:
        warnings.append("Resume may be too long (aim for 1-2 pages)")
        score -= 10

    # Check for bullet points (good for ATS)
    if '•' in resume_text or '◦' in resume_text or re.search(r'^\s*[-*]\s', resume_text, re.MULTILINE):
        score += 5  # Bonus for using bullet points

    return max(score, 0), warnings


def calculate_ats_score(
    resume_text: str,
    job_description: str,
    jd_skills: list[str]
) -> dict:
    """
    Calculate overall ATS score with weighted breakdown.

    With Job Description (weights):
      - 40% Skill Match
      - 30% Keyword Match
      - 20% Experience Match
      - 10% Formatting & Structure

    Without Job Description (weights shift to resume quality):
      - 20% Skills Present (general check)
      - 20% Content Quality
      - 30% Experience Section
      - 30% Formatting & Structure
    """
    has_jd = bool(job_description and job_description.strip())

    # Calculate individual scores
    skill_score, matched_skills, missing_skills = calculate_skill_match(resume_text, jd_skills)
    keyword_score, keyword_matched, keyword_total = calculate_keyword_match(resume_text, job_description)
    experience_score, experience_note = calculate_experience_match(resume_text, job_description)
    formatting_score, formatting_warnings = calculate_formatting_score(resume_text)

    if has_jd:
        # With JD: Focus on matching
        skill_weight = 0.40
        keyword_weight = 0.30
        exp_weight = 0.20
        format_weight = 0.10
    else:
        # Without JD: Focus on resume quality and ATS-friendliness
        skill_weight = 0.20
        keyword_weight = 0.20
        exp_weight = 0.30
        format_weight = 0.30

        # Adjust scores for no-JD mode
        # Check if resume has good skill representation
        skill_score = calculate_general_skills_score(resume_text)
        keyword_score = calculate_content_quality_score(resume_text)
        experience_note = "General experience evaluation (no JD provided)"

    # Calculate weighted final score
    final_score = int(
        (skill_score * skill_weight) +
        (keyword_score * keyword_weight) +
        (experience_score * exp_weight) +
        (formatting_score * format_weight)
    )

    return {
        "final_score": final_score,
        "breakdown": {
            "skill_match": {
                "score": skill_score,
                "weight": int(skill_weight * 100),
                "weighted_score": int(skill_score * skill_weight),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills
            },
            "keyword_match": {
                "score": keyword_score,
                "weight": int(keyword_weight * 100),
                "weighted_score": int(keyword_score * keyword_weight),
                "matched_count": keyword_matched,
                "total_keywords": keyword_total
            },
            "experience_match": {
                "score": experience_score,
                "weight": int(exp_weight * 100),
                "weighted_score": int(experience_score * exp_weight),
                "note": experience_note
            },
            "formatting": {
                "score": formatting_score,
                "weight": int(format_weight * 100),
                "weighted_score": int(formatting_score * format_weight),
                "warnings": formatting_warnings
            }
        }
    }


def calculate_general_skills_score(resume_text: str) -> int:
    """Calculate a general skills score when no JD is provided."""
    resume_lower = resume_text.lower()
    score = 50  # Base score

    # Check for common skills section
    if any(term in resume_lower for term in ['skills', 'technologies', 'technical skills']):
        score += 15

    # Check for variety of technical terms
    tech_terms = ['python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
                  'react', 'node', 'git', 'agile', 'scrum', 'api', 'database', 'cloud',
                  'machine learning', 'data', 'analytics', 'devops', 'ci/cd']
    found_terms = sum(1 for term in tech_terms if term in resume_lower)

    if found_terms >= 8:
        score += 25
    elif found_terms >= 5:
        score += 15
    elif found_terms >= 2:
        score += 10

    # Check for soft skills
    soft_skills = ['leadership', 'communication', 'teamwork', 'problem-solving', 'analytical']
    found_soft = sum(1 for s in soft_skills if s in resume_lower)
    if found_soft >= 2:
        score += 10

    return min(score, 100)


def calculate_content_quality_score(resume_text: str) -> int:
    """Calculate content quality score when no JD is provided."""
    resume_lower = resume_text.lower()
    score = 50  # Base score

    # Check for quantifiable achievements
    if re.search(r'\d+%|\$[\d,]+|\d+x|\d+\s*(users?|customers?|clients?)', resume_lower):
        score += 20

    # Check for action verbs
    action_verbs = ['led', 'developed', 'implemented', 'managed', 'created', 'designed',
                    'built', 'optimized', 'increased', 'decreased', 'achieved', 'delivered']
    verb_count = sum(1 for verb in action_verbs if verb in resume_lower)
    if verb_count >= 5:
        score += 20
    elif verb_count >= 2:
        score += 10

    # Check for bullet points
    if '•' in resume_text or re.search(r'^\s*[-*]\s', resume_text, re.MULTILINE):
        score += 10

    return min(score, 100)
