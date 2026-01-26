"""
Resume Section Analysis Service - Analyzes individual resume sections.

Sections analyzed:
- Contact Information
- Professional Summary
- Work Experience
- Skills
- Education
- Projects (if present)
"""

import re
from typing import Tuple


def analyze_contact_section(resume_text: str) -> dict:
    """Analyze contact information section."""
    resume_lower = resume_text.lower()
    score = 0
    improvements = []
    issues = []

    # Check for email
    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text))
    if has_email:
        score += 25
    else:
        issues.append("Missing email address")

    # Check for phone
    has_phone = bool(re.search(r'[\d\-\(\)\+\s]{10,}', resume_text))
    if has_phone:
        score += 25
    else:
        issues.append("Missing phone number")

    # Check for LinkedIn
    has_linkedin = 'linkedin' in resume_lower
    if has_linkedin:
        score += 25
    else:
        improvements.append("Add LinkedIn profile URL")

    # Check for location (city/state)
    location_patterns = [
        r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
        r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b',  # City, State
    ]
    has_location = any(re.search(p, resume_text) for p in location_patterns)
    if has_location:
        score += 15
    else:
        improvements.append("Add city/state location")

    # Check for GitHub/Portfolio (bonus)
    has_portfolio = any(x in resume_lower for x in ['github', 'portfolio', 'gitlab', 'website'])
    if has_portfolio:
        score += 10

    return {
        "name": "Contact Information",
        "icon": "mail",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_summary_section(resume_text: str) -> dict:
    """Analyze professional summary section."""
    resume_lower = resume_text.lower()
    score = 50  # Base score
    improvements = []
    issues = []

    # Check for summary/objective section
    summary_patterns = [
        r'(summary|objective|profile|about)\s*[\n:]',
        r'professional\s+(summary|profile)',
    ]
    has_summary = any(re.search(p, resume_lower) for p in summary_patterns)

    if has_summary:
        score += 20

        # Check summary length (ideal: 2-4 sentences)
        # Find the summary section content
        summary_match = re.search(
            r'(summary|objective|profile|about)[\s\n:]+([^\n]+(?:\n[^\n]+){0,4})',
            resume_lower
        )
        if summary_match:
            summary_text = summary_match.group(2)
            word_count = len(summary_text.split())

            if 30 <= word_count <= 80:
                score += 20
            elif word_count < 30:
                improvements.append("Expand summary to 2-4 sentences")
            else:
                improvements.append("Consider shortening summary")

        # Check for quantifiable achievements in summary
        if re.search(r'\d+[%+]|\$\d+|\d+\s*(years?|projects?|clients?)', resume_lower[:500]):
            score += 10
        else:
            improvements.append("Add quantifiable achievements")
    else:
        issues.append("Missing professional summary section")
        score = 30

    return {
        "name": "Professional Summary",
        "icon": "file-text",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_experience_section(resume_text: str, job_description: str) -> dict:
    """Analyze work experience section."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    score = 40  # Base score
    improvements = []
    issues = []

    # Check for experience section
    exp_patterns = [
        r'(experience|employment|work\s*history)',
        r'professional\s+experience',
    ]
    has_experience = any(re.search(p, resume_lower) for p in exp_patterns)

    if not has_experience:
        issues.append("Missing work experience section")
        return {
            "name": "Work Experience",
            "icon": "briefcase",
            "score": 20,
            "improvements": improvements,
            "issues": issues
        }

    score += 15

    # Check for bullet points (ATS-friendly)
    has_bullets = bool(re.search(r'[•◦\-\*]\s+\w', resume_text))
    if has_bullets:
        score += 10
    else:
        improvements.append("Use bullet points for achievements")

    # Check for action verbs
    action_verbs = ['led', 'developed', 'implemented', 'managed', 'created', 'designed',
                    'built', 'launched', 'optimized', 'increased', 'decreased', 'achieved',
                    'delivered', 'improved', 'streamlined', 'automated', 'analyzed']
    verb_count = sum(1 for verb in action_verbs if verb in resume_lower)
    if verb_count >= 5:
        score += 15
    elif verb_count >= 2:
        score += 8
        improvements.append("Use more action verbs (Led, Developed, Implemented)")
    else:
        improvements.append("Start bullets with strong action verbs")

    # Check for quantifiable results
    has_numbers = bool(re.search(r'\d+[%+]|\$[\d,]+|\d+x|\d+\s*(users?|customers?|clients?)', resume_lower))
    if has_numbers:
        score += 15
    else:
        improvements.append("Add quantifiable achievements (%, $, numbers)")

    # Check for dates
    has_dates = bool(re.search(r'(19|20)\d{2}', resume_text))
    if has_dates:
        score += 5
    else:
        issues.append("Add employment dates")

    return {
        "name": "Work Experience",
        "icon": "briefcase",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_skills_section(resume_text: str, jd_skills: list[str]) -> dict:
    """Analyze skills section."""
    resume_lower = resume_text.lower()
    score = 40  # Base score
    improvements = []
    issues = []

    # Check for skills section
    has_skills_section = any(x in resume_lower for x in ['skills', 'technologies', 'technical skills', 'competencies'])

    if not has_skills_section:
        issues.append("Missing dedicated skills section")
        return {
            "name": "Skills",
            "icon": "code",
            "score": 25,
            "improvements": ["Add a skills section"],
            "issues": issues
        }

    score += 15

    # Check skill match with JD
    if jd_skills:
        matched_count = sum(1 for skill in jd_skills if skill.lower() in resume_lower)
        match_ratio = matched_count / len(jd_skills) if jd_skills else 0

        if match_ratio >= 0.7:
            score += 30
        elif match_ratio >= 0.4:
            score += 20
            improvements.append("Add more skills from job description")
        else:
            score += 10
            improvements.append("Skills don't match job requirements well")

    # Check for skill categories (organized)
    categories = ['programming', 'languages', 'frameworks', 'tools', 'databases', 'soft skills']
    has_categories = sum(1 for cat in categories if cat in resume_lower) >= 2
    if has_categories:
        score += 10
    else:
        improvements.append("Organize skills by category")

    return {
        "name": "Skills",
        "icon": "code",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_education_section(resume_text: str) -> dict:
    """Analyze education section."""
    resume_lower = resume_text.lower()
    score = 40  # Base score
    improvements = []
    issues = []

    # Check for education section
    has_education = any(x in resume_lower for x in ['education', 'degree', 'university', 'college', 'bachelor', 'master', 'phd'])

    if not has_education:
        issues.append("Missing education section")
        return {
            "name": "Education",
            "icon": "graduation-cap",
            "score": 20,
            "improvements": improvements,
            "issues": issues
        }

    score += 20

    # Check for degree
    degrees = ['bachelor', 'master', 'phd', 'associate', 'b.s.', 'b.a.', 'm.s.', 'm.a.', 'mba']
    has_degree = any(d in resume_lower for d in degrees)
    if has_degree:
        score += 20
    else:
        improvements.append("Specify degree type")

    # Check for graduation year
    has_grad_year = bool(re.search(r'(19|20)\d{2}', resume_text))
    if has_grad_year:
        score += 10
    else:
        improvements.append("Add graduation year")

    # Check for GPA (if recent graduate)
    has_gpa = 'gpa' in resume_lower or bool(re.search(r'\d\.\d{1,2}\s*/\s*4', resume_text))
    if has_gpa:
        score += 10

    return {
        "name": "Education",
        "icon": "graduation-cap",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_certifications_section(resume_text: str, job_description: str) -> dict:
    """Analyze certifications section."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    score = 40  # Base score
    improvements = []
    issues = []

    # Check for certifications section
    cert_patterns = ['certification', 'certified', 'certificate', 'license', 'credential']
    has_cert_section = any(x in resume_lower for x in cert_patterns)

    if not has_cert_section:
        # Check if JD mentions certifications
        jd_wants_certs = any(x in jd_lower for x in cert_patterns)
        if jd_wants_certs:
            issues.append("JD mentions certifications but none found in resume")
            return {
                "name": "Certifications",
                "icon": "award",
                "score": 15,
                "improvements": ["Add certifications mentioned in job description"],
                "issues": issues
            }
        else:
            # No certs in resume, JD doesn't explicitly require them
            return {
                "name": "Certifications",
                "icon": "award",
                "score": 30,
                "improvements": ["Add relevant certifications to strengthen your profile"],
                "issues": ["No certifications section found"]
            }

    score += 20

    # Common industry certifications to check
    common_certs = [
        'aws', 'azure', 'gcp', 'google cloud',
        'pmp', 'scrum', 'agile', 'csm',
        'cissp', 'cisa', 'security+', 'comptia',
        'ccna', 'ccnp', 'cisco',
        'cpa', 'cfa', 'series',
        'six sigma', 'lean',
        'itil', 'prince2',
        'salesforce', 'hubspot',
        'kubernetes', 'docker', 'cka', 'ckad'
    ]

    found_certs = [cert for cert in common_certs if cert in resume_lower]

    if len(found_certs) >= 3:
        score += 25
    elif len(found_certs) >= 1:
        score += 15
    else:
        improvements.append("Add industry-recognized certifications")

    # Check if certifications match JD requirements
    jd_certs = [cert for cert in common_certs if cert in jd_lower]
    if jd_certs:
        matched_certs = [cert for cert in jd_certs if cert in resume_lower]
        if len(matched_certs) == len(jd_certs):
            score += 15
        elif len(matched_certs) > 0:
            score += 10
            missing = [c for c in jd_certs if c not in resume_lower]
            if missing:
                improvements.append(f"Consider adding: {', '.join(missing[:3])}")
        else:
            improvements.append("Add certifications mentioned in job description")

    # Check for dates/validity
    has_cert_dates = bool(re.search(r'(issued|expires?|valid|20\d{2})', resume_lower))
    if has_cert_dates:
        score += 5
    else:
        improvements.append("Add certification dates/validity")

    return {
        "name": "Certifications",
        "icon": "award",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_formatting(resume_text: str) -> dict:
    """Analyze overall formatting and structure."""
    score = 50  # Base score
    improvements = []
    issues = []

    # Check length
    word_count = len(resume_text.split())
    if 300 <= word_count <= 800:
        score += 20
    elif word_count < 300:
        issues.append("Resume too short")
    elif word_count > 1200:
        improvements.append("Consider condensing to 1-2 pages")
    else:
        score += 10

    # Check for consistent formatting (bullet points)
    bullet_types = [
        len(re.findall(r'•', resume_text)),
        len(re.findall(r'◦', resume_text)),
        len(re.findall(r'^\s*[-]\s', resume_text, re.MULTILINE)),
        len(re.findall(r'^\s*[*]\s', resume_text, re.MULTILINE)),
    ]
    if max(bullet_types) > 0 and sum(1 for b in bullet_types if b > 0) == 1:
        score += 15  # Consistent bullet style
    elif max(bullet_types) > 0:
        improvements.append("Use consistent bullet point style")
        score += 5

    # Check section headers
    sections_found = 0
    for section in ['experience', 'education', 'skills', 'summary', 'projects']:
        if section in resume_text.lower():
            sections_found += 1

    if sections_found >= 4:
        score += 15
    elif sections_found >= 3:
        score += 10
    else:
        improvements.append("Add clear section headers")

    return {
        "name": "Formatting & Structure",
        "icon": "layout",
        "score": min(score, 100),
        "improvements": improvements,
        "issues": issues
    }


def analyze_all_sections(resume_text: str, job_description: str, jd_skills: list[str]) -> list[dict]:
    """Analyze all resume sections and return scores."""
    sections = [
        analyze_contact_section(resume_text),
        analyze_summary_section(resume_text),
        analyze_experience_section(resume_text, job_description),
        analyze_skills_section(resume_text, jd_skills),
        analyze_education_section(resume_text),
        analyze_certifications_section(resume_text, job_description),
        analyze_formatting(resume_text),
    ]

    # Calculate overall score (weighted average)
    # Contact 8%, Summary 12%, Experience 28%, Skills 23%, Education 10%, Certs 10%, Formatting 9%
    weights = [0.08, 0.12, 0.28, 0.23, 0.10, 0.10, 0.09]
    overall_score = sum(s["score"] * w for s, w in zip(sections, weights))

    return {
        "overall_score": int(overall_score),
        "sections": sections,
        "total_sections": len(sections),
        "total_improvements": sum(len(s["improvements"]) for s in sections),
        "total_issues": sum(len(s["issues"]) for s in sections)
    }
