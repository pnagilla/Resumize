"""
Resume Section Analysis Service - Analyzes individual resume sections.

Sections analyzed:
- Contact Information
- Professional Summary
- Work Experience
- Skills
- Education
- Certifications
- Formatting & Structure
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
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
    if email_match:
        email = email_match.group().lower()
        score += 20
        # Check for unprofessional email
        unprofessional_patterns = ['69', '420', 'sexy', 'hot', 'babe', 'cool', 'xxx']
        if any(p in email for p in unprofessional_patterns):
            issues.append("Email address appears unprofessional")
            score -= 10
        # Check for numbers in email (often unprofessional)
        if re.search(r'\d{3,}', email.split('@')[0]):
            improvements.append("Consider using a more professional email without excessive numbers")
    else:
        issues.append("Missing email address - critical for recruiter contact")

    # Check for phone
    phone_match = re.search(r'[\d\-\(\)\+\s]{10,}', resume_text)
    if phone_match:
        score += 20
    else:
        issues.append("Missing phone number - recruiters need multiple contact methods")

    # Check for LinkedIn
    has_linkedin = 'linkedin' in resume_lower or 'linkedin.com' in resume_lower
    if has_linkedin:
        score += 20
        # Check if it's a custom URL
        if not re.search(r'linkedin\.com/in/[\w-]+', resume_lower):
            improvements.append("Use a custom LinkedIn URL (linkedin.com/in/yourname)")
    else:
        issues.append("Missing LinkedIn profile - 87% of recruiters use LinkedIn")

    # Check for location (city/state)
    location_patterns = [
        r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
        r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b',  # City, State
    ]
    has_location = any(re.search(p, resume_text) for p in location_patterns)
    if has_location:
        score += 15
    else:
        improvements.append("Add city/state location for local job matching")

    # Check for GitHub/Portfolio (important for tech roles)
    has_github = 'github' in resume_lower or 'github.com' in resume_lower
    has_portfolio = any(x in resume_lower for x in ['portfolio', 'website', 'personal site'])

    if has_github:
        score += 15
    else:
        improvements.append("Add GitHub profile to showcase your code")

    if has_portfolio:
        score += 10
    else:
        improvements.append("Consider adding a portfolio website")

    # Check for full name at top
    lines = resume_text.strip().split('\n')
    if lines:
        first_line = lines[0].strip()
        # Name should be short and at the top
        if len(first_line.split()) > 4 or len(first_line) > 50:
            improvements.append("Ensure your full name is prominently displayed at the top")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Add more contact methods to make it easier for recruiters to reach you")

    return {
        "name": "Contact Information",
        "icon": "mail",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_summary_section(resume_text: str, job_description: str = "") -> dict:
    """Analyze professional summary section."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower() if job_description else ""
    score = 30  # Lower base score
    improvements = []
    issues = []

    # Check for summary/objective section
    summary_patterns = [
        r'(summary|objective|profile|about)\s*[\n:]',
        r'professional\s+(summary|profile)',
        r'career\s+(summary|objective)',
    ]
    has_summary = any(re.search(p, resume_lower) for p in summary_patterns)

    if not has_summary:
        issues.append("Missing professional summary - this is the first thing recruiters read")
        return {
            "name": "Professional Summary",
            "icon": "file-text",
            "score": 20,
            "improvements": ["Add a compelling 2-4 sentence professional summary"],
            "issues": issues
        }

    score += 15

    # Find the summary section content
    summary_match = re.search(
        r'(summary|objective|profile|about)[\s\n:]+([^\n]+(?:\n[^\n]+){0,5})',
        resume_lower
    )

    if summary_match:
        summary_text = summary_match.group(2)
        word_count = len(summary_text.split())

        # Check summary length
        if word_count < 20:
            issues.append("Summary too short - aim for 50-100 words")
        elif word_count > 150:
            issues.append("Summary too long - recruiters spend 6 seconds on initial scan")
            improvements.append("Condense summary to 2-4 impactful sentences")
        elif 30 <= word_count <= 100:
            score += 15
        else:
            # word count 20-29 or 101-149 - not ideal
            improvements.append("Optimize summary length to 50-100 words for best impact")

        # Check for first-person pronouns (should avoid "I", "me", "my")
        first_person_count = len(re.findall(r'\b(i|me|my|myself)\b', summary_text))
        if first_person_count > 2:
            improvements.append("Reduce first-person pronouns (I, me, my) - use action-oriented language")

        # Check for weak/filler words
        weak_words = ['responsible for', 'duties included', 'helped', 'assisted',
                      'worked on', 'was involved', 'various', 'multiple', 'etc']
        found_weak = [w for w in weak_words if w in summary_text]
        if found_weak:
            improvements.append(f"Replace weak phrases: '{found_weak[0]}' with stronger action words")

        # Check for generic statements
        generic_phrases = ['hard worker', 'team player', 'detail-oriented', 'self-starter',
                         'fast learner', 'go-getter', 'think outside the box', 'synergy']
        found_generic = [p for p in generic_phrases if p in summary_text]
        if found_generic:
            issues.append(f"Avoid cliches like '{found_generic[0]}' - be specific about your skills")

        # Check for quantifiable achievements
        has_numbers = bool(re.search(r'\d+[%+]|\$[\d,]+|\d+\s*(years?|projects?|clients?|teams?)', summary_text))
        if has_numbers:
            score += 15
        else:
            improvements.append("Add specific metrics (e.g., '5+ years experience', 'led team of 10')")

        # Check for job title alignment with JD
        if jd_lower:
            # Extract potential job titles from JD
            jd_title_match = re.search(r'(senior|junior|lead|principal|staff)?\s*(software|data|product|project|marketing|sales|design)\s*(engineer|developer|manager|analyst|scientist|designer)', jd_lower)
            if jd_title_match:
                jd_title = jd_title_match.group()
                if jd_title not in summary_text:
                    improvements.append(f"Consider mentioning target role '{jd_title}' in summary")

        # Check for industry keywords from JD
        if jd_lower:
            jd_keywords = set(re.findall(r'\b[a-z]{4,}\b', jd_lower))
            summary_keywords = set(re.findall(r'\b[a-z]{4,}\b', summary_text))
            common_keywords = jd_keywords.intersection(summary_keywords)
            if len(common_keywords) < 3:
                improvements.append("Include more keywords from the job description in your summary")
            else:
                score += 10
        else:
            # No JD provided - give general advice
            improvements.append("Tailor your summary with keywords from target job descriptions")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Strengthen your summary with more specific achievements and industry keywords")

    return {
        "name": "Professional Summary",
        "icon": "file-text",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_experience_section(resume_text: str, job_description: str) -> dict:
    """Analyze work experience section."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower() if job_description else ""
    score = 25  # Lower base score
    improvements = []
    issues = []

    # Check for experience section
    exp_patterns = [
        r'(experience|employment|work\s*history)',
        r'professional\s+experience',
    ]
    has_experience = any(re.search(p, resume_lower) for p in exp_patterns)

    if not has_experience:
        issues.append("Missing work experience section - this is the most important section")
        return {
            "name": "Work Experience",
            "icon": "briefcase",
            "score": 15,
            "improvements": ["Add a work experience section with your relevant positions"],
            "issues": issues
        }

    score += 10

    # Check for bullet points (ATS-friendly)
    bullet_count = len(re.findall(r'[•◦\-\*]\s+\w', resume_text))
    if bullet_count >= 10:
        score += 10
    elif bullet_count >= 5:
        score += 5
        improvements.append("Add more bullet points to describe your achievements (aim for 3-5 per role)")
    elif bullet_count > 0:
        score += 2
        improvements.append("Use more bullet points for achievements - aim for 3-5 per role")
    else:
        issues.append("No bullet points found - ATS systems prefer bulleted achievements")

    # Check for action verbs at start of bullets
    strong_verbs = ['led', 'developed', 'implemented', 'managed', 'created', 'designed',
                    'built', 'launched', 'optimized', 'increased', 'decreased', 'achieved',
                    'delivered', 'improved', 'streamlined', 'automated', 'analyzed',
                    'spearheaded', 'orchestrated', 'pioneered', 'transformed', 'drove',
                    'accelerated', 'reduced', 'generated', 'established', 'negotiated']

    weak_verbs = ['helped', 'assisted', 'worked', 'was responsible', 'handled', 'did', 'made']

    verb_count = sum(1 for verb in strong_verbs if verb in resume_lower)
    weak_verb_count = sum(1 for verb in weak_verbs if verb in resume_lower)

    if verb_count >= 8:
        score += 15
    elif verb_count >= 4:
        score += 8
        improvements.append("Use stronger action verbs (Spearheaded, Orchestrated, Pioneered)")
    else:
        issues.append("Missing strong action verbs - start bullets with impactful verbs like Led, Developed, Implemented")

    if weak_verb_count > 2:
        improvements.append("Replace weak verbs like 'helped', 'assisted', 'worked on' with stronger alternatives")

    # Check for quantifiable results (CRITICAL)
    metrics_patterns = [
        r'\d+%',  # percentages
        r'\$[\d,]+[KMB]?',  # dollar amounts
        r'\d+x',  # multipliers
        r'\d+\+?\s*(users?|customers?|clients?|members?|employees?)',  # people counts
        r'\d+\+?\s*(projects?|products?|features?|applications?)',  # project counts
        r'#\d+',  # rankings
        r'\d+\s*(hours?|days?|weeks?|months?)',  # time savings
    ]

    metrics_found = sum(1 for p in metrics_patterns if re.search(p, resume_lower))

    if metrics_found >= 5:
        score += 20
    elif metrics_found >= 3:
        score += 12
        improvements.append("Add more quantifiable metrics (revenue %, time saved, team size)")
    elif metrics_found >= 1:
        score += 5
        improvements.append("Most bullets lack metrics - quantify your impact with specific numbers")
    else:
        issues.append("No metrics found - quantify achievements (e.g., 'Increased efficiency by 30%')")

    # Check for dates
    date_patterns = [
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}',
        r'\d{1,2}/\d{4}',
        r'(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}|present',
    ]
    has_dates = any(re.search(p, resume_lower) for p in date_patterns)
    if has_dates:
        score += 5
    else:
        issues.append("Missing employment dates - required for ATS and recruiters")

    # Check for company names
    company_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Ltd|Co)\.?)?\b'
    companies = re.findall(company_pattern, resume_text)
    if len(companies) < 2:
        improvements.append("Ensure company names are clearly visible for each position")

    # Check for job titles
    title_keywords = ['engineer', 'developer', 'manager', 'analyst', 'designer', 'director',
                     'coordinator', 'specialist', 'consultant', 'architect', 'lead', 'intern']
    has_titles = sum(1 for t in title_keywords if t in resume_lower)
    if has_titles < 1:
        improvements.append("Include clear job titles for each position")
    else:
        score += 5

    # Check for relevance to JD
    if jd_lower:
        jd_keywords = set(re.findall(r'\b[a-z]{4,}\b', jd_lower))
        exp_keywords = set(re.findall(r'\b[a-z]{4,}\b', resume_lower))
        overlap = len(jd_keywords.intersection(exp_keywords))
        if overlap < 10:
            improvements.append("Tailor experience bullets to include more keywords from job description")
        elif overlap >= 20:
            score += 10
        else:
            # overlap 10-19 - partial match
            improvements.append("Add more job-specific keywords from the job description to your experience section")
    else:
        # No JD - give general advice
        improvements.append("Customize your experience bullets with keywords from your target job descriptions")

    # Check for passive voice
    passive_patterns = ['was created', 'were developed', 'was managed', 'been involved', 'was responsible']
    passive_count = sum(1 for p in passive_patterns if p in resume_lower)
    if passive_count > 2:
        improvements.append("Convert passive voice to active voice (e.g., 'was developed' → 'developed')")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Add more quantifiable achievements and industry-specific keywords to strengthen this section")

    return {
        "name": "Work Experience",
        "icon": "briefcase",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_skills_section(resume_text: str, jd_skills: list[str]) -> dict:
    """Analyze skills section."""
    resume_lower = resume_text.lower()
    score = 25  # Lower base score
    improvements = []
    issues = []

    # Check for skills section
    skills_headers = ['skills', 'technologies', 'technical skills', 'competencies',
                      'core competencies', 'expertise', 'proficiencies']
    has_skills_section = any(x in resume_lower for x in skills_headers)

    if not has_skills_section:
        issues.append("Missing dedicated skills section - ATS systems scan for this")
        return {
            "name": "Skills",
            "icon": "code",
            "score": 15,
            "improvements": ["Add a clear skills section with relevant technologies"],
            "issues": issues
        }

    score += 15

    # Check skill match with JD (CRITICAL)
    if jd_skills:
        matched_skills = [skill for skill in jd_skills if skill.lower() in resume_lower]
        missing_skills = [skill for skill in jd_skills if skill.lower() not in resume_lower]
        match_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 0

        if match_ratio >= 0.8:
            score += 30
        elif match_ratio >= 0.6:
            score += 20
            if missing_skills[:3]:
                improvements.append(f"Add missing skills: {', '.join(missing_skills[:3])}")
        elif match_ratio >= 0.4:
            score += 10
            issues.append(f"Low skill match ({int(match_ratio*100)}%) - add: {', '.join(missing_skills[:5])}")
        else:
            issues.append(f"Critical: Only {int(match_ratio*100)}% skill match with job requirements")
            if missing_skills[:5]:
                improvements.append(f"Must add: {', '.join(missing_skills[:5])}")
    else:
        # No JD skills provided - general advice
        improvements.append("Match your skills section to keywords in target job descriptions")

    # Check for skill organization/categories
    categories = ['programming', 'languages', 'frameworks', 'tools', 'databases',
                  'cloud', 'devops', 'frontend', 'backend', 'soft skills', 'methodologies']
    found_categories = sum(1 for cat in categories if cat in resume_lower)

    if found_categories >= 3:
        score += 10
    elif found_categories >= 1:
        score += 5
        improvements.append("Organize skills into clear categories (Languages, Frameworks, Tools)")
    else:
        improvements.append("Group skills by category for better readability and ATS parsing")

    # Check for outdated technologies
    outdated_tech = ['jquery', 'flash', 'actionscript', 'cobol', 'fortran', 'vb6',
                     'dreamweaver', 'frontpage', 'coldfusion']
    found_outdated = [t for t in outdated_tech if t in resume_lower]
    if found_outdated:
        improvements.append(f"Consider removing outdated skills: {', '.join(found_outdated)}")

    # Check for proficiency levels
    proficiency_words = ['proficient', 'expert', 'advanced', 'intermediate', 'beginner',
                         'familiar', 'experienced']
    has_proficiency = any(p in resume_lower for p in proficiency_words)
    if not has_proficiency:
        improvements.append("Consider adding proficiency levels for key skills")

    # Check for soft skills vs hard skills balance
    soft_skills = ['communication', 'leadership', 'teamwork', 'problem-solving', 'analytical',
                   'presentation', 'time management', 'collaboration']
    hard_skills_indicators = ['python', 'java', 'sql', 'aws', 'react', 'node', 'docker']

    soft_count = sum(1 for s in soft_skills if s in resume_lower)
    hard_count = sum(1 for s in hard_skills_indicators if s in resume_lower)

    if soft_count > 0 and hard_count > 0:
        score += 5
    elif soft_count == 0:
        improvements.append("Add relevant soft skills (Communication, Leadership, Problem-solving)")
    elif hard_count == 0:
        improvements.append("Add more technical/hard skills relevant to the role")

    # Check skill count
    skill_list_match = re.findall(r'\b[A-Za-z+#]+(?:\s+[A-Za-z]+)?\b(?=\s*[,|•]|\s*$)', resume_text)
    if len(skill_list_match) < 8:
        improvements.append("Add more relevant skills - aim for 15-25 key skills")
    elif len(skill_list_match) < 15:
        score += 5
        improvements.append("Consider adding a few more relevant skills to strengthen this section")
    else:
        score += 10

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Expand your skills section with more industry-relevant technologies")

    return {
        "name": "Skills",
        "icon": "code",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_education_section(resume_text: str) -> dict:
    """Analyze education section."""
    resume_lower = resume_text.lower()
    score = 30  # Base score
    improvements = []
    issues = []

    # Check for education section
    edu_keywords = ['education', 'degree', 'university', 'college', 'bachelor', 'master',
                    'phd', 'diploma', 'academic']
    has_education = any(x in resume_lower for x in edu_keywords)

    if not has_education:
        issues.append("Missing education section")
        return {
            "name": "Education",
            "icon": "graduation-cap",
            "score": 20,
            "improvements": ["Add education section with degree, school, and graduation year"],
            "issues": issues
        }

    score += 15

    # Check for degree type
    degrees = {
        'high': ['phd', 'doctorate', 'doctor of'],
        'masters': ['master', 'm.s.', 'm.a.', 'mba', 'm.sc', 'msc'],
        'bachelors': ['bachelor', 'b.s.', 'b.a.', 'b.sc', 'bsc', 'b.eng'],
        'associate': ['associate', 'a.s.', 'a.a.'],
    }

    degree_found = None
    for level, patterns in degrees.items():
        if any(d in resume_lower for d in patterns):
            degree_found = level
            break

    if degree_found:
        score += 15
    else:
        improvements.append("Clearly specify your degree type (Bachelor's, Master's, etc.)")

    # Check for school name
    university_keywords = ['university', 'college', 'institute', 'school of']
    has_school = any(k in resume_lower for k in university_keywords)
    if has_school:
        score += 10
    else:
        improvements.append("Include the full name of your educational institution")

    # Check for field of study
    fields = ['computer science', 'engineering', 'business', 'mathematics', 'physics',
              'economics', 'marketing', 'finance', 'information technology', 'data science']
    has_field = any(f in resume_lower for f in fields)
    if has_field:
        score += 10
    else:
        improvements.append("Include your major/field of study")

    # Check for graduation year
    grad_year_match = re.search(r'(19|20)\d{2}', resume_text)
    if grad_year_match:
        score += 5
        year = int(grad_year_match.group())
        # If recent grad (within 3 years), look for GPA
        if year >= 2022:
            has_gpa = 'gpa' in resume_lower or bool(re.search(r'\d\.\d{1,2}\s*/?\s*4', resume_text))
            if has_gpa:
                score += 10
            else:
                improvements.append("Recent graduates should include GPA if 3.0 or higher")
    else:
        improvements.append("Add graduation year (or expected graduation date)")

    # Check for honors/achievements
    honors = ['cum laude', 'magna cum laude', 'summa cum laude', 'honors', 'dean\'s list',
              'scholarship', 'fellowship', 'award', 'distinction']
    has_honors = any(h in resume_lower for h in honors)
    if has_honors:
        score += 5
    else:
        improvements.append("Include academic honors, awards, or relevant scholarships if applicable")

    # Check for relevant coursework (good for entry-level)
    has_coursework = any(x in resume_lower for x in ['coursework', 'relevant courses', 'courses'])
    if not has_coursework and degree_found in ['bachelors', 'associate']:
        improvements.append("Consider adding relevant coursework for entry-level positions")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Add more details like GPA, honors, or relevant coursework to strengthen this section")

    return {
        "name": "Education",
        "icon": "graduation-cap",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_certifications_section(resume_text: str, job_description: str) -> dict:
    """Analyze certifications section."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower() if job_description else ""
    score = 20  # Low base - certs are often missing
    improvements = []
    issues = []

    # Check for certifications section
    cert_patterns = ['certification', 'certified', 'certificate', 'license', 'credential', 'accreditation']
    has_cert_section = any(x in resume_lower for x in cert_patterns)

    # Check if JD mentions certifications
    jd_wants_certs = any(x in jd_lower for x in cert_patterns) if jd_lower else False

    if not has_cert_section:
        if jd_wants_certs:
            issues.append("Job requires certifications but none found in resume")
            return {
                "name": "Certifications",
                "icon": "award",
                "score": 10,
                "improvements": ["Add certifications mentioned in the job description"],
                "issues": issues
            }
        else:
            return {
                "name": "Certifications",
                "icon": "award",
                "score": 25,
                "improvements": ["Add relevant industry certifications to stand out from other candidates"],
                "issues": ["No certifications section found"]
            }

    score += 25

    # Common industry certifications to check
    common_certs = {
        'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'cloud practitioner', 'solutions architect'],
        'project_mgmt': ['pmp', 'scrum', 'agile', 'csm', 'safe', 'prince2', 'capm'],
        'security': ['cissp', 'cisa', 'security+', 'comptia', 'ceh', 'oscp'],
        'networking': ['ccna', 'ccnp', 'cisco', 'network+'],
        'data': ['tableau', 'power bi', 'google analytics', 'data science'],
        'devops': ['kubernetes', 'docker', 'cka', 'ckad', 'terraform', 'jenkins'],
        'other': ['six sigma', 'lean', 'itil', 'salesforce', 'hubspot']
    }

    found_certs = []
    for category, certs in common_certs.items():
        for cert in certs:
            if cert in resume_lower:
                found_certs.append(cert)

    if len(found_certs) >= 4:
        score += 30
    elif len(found_certs) >= 2:
        score += 20
    elif len(found_certs) >= 1:
        score += 10
        improvements.append("Add more industry-recognized certifications to strengthen your credentials")
    else:
        improvements.append("Add industry-recognized certifications (AWS, PMP, Scrum, etc.)")

    # Check if certifications match JD requirements
    if jd_lower:
        jd_certs = []
        for category, certs in common_certs.items():
            for cert in certs:
                if cert in jd_lower:
                    jd_certs.append(cert)

        if jd_certs:
            matched_certs = [cert for cert in jd_certs if cert in resume_lower]
            missing_certs = [cert for cert in jd_certs if cert not in resume_lower]

            if len(matched_certs) == len(jd_certs):
                score += 15
            elif len(matched_certs) > 0:
                score += 8
                if missing_certs:
                    improvements.append(f"Job mentions: {', '.join(missing_certs[:3])} - consider obtaining these")
            else:
                issues.append(f"Missing required certifications: {', '.join(jd_certs[:3])}")
    else:
        # No JD - general advice
        improvements.append("Pursue certifications that align with your target roles")

    # Check for expiration dates
    has_dates = bool(re.search(r'(issued|expires?|valid|earned|obtained)\s*:?\s*(19|20)\d{2}', resume_lower))
    if has_dates:
        score += 5
    else:
        improvements.append("Include certification dates (issued/expiry) to show current status")

    # Check for certification IDs/verification
    has_id = bool(re.search(r'(id|credential|badge|verify)[:\s]*\w+', resume_lower))
    if has_id:
        score += 5
    else:
        improvements.append("Include certification ID numbers for verification")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Add more certifications and include verification details")

    return {
        "name": "Certifications",
        "icon": "award",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_formatting(resume_text: str) -> dict:
    """Analyze overall formatting and structure."""
    score = 35  # Base score
    improvements = []
    issues = []

    # Check length
    word_count = len(resume_text.split())
    if 400 <= word_count <= 700:
        score += 15
    elif 300 <= word_count < 400:
        score += 10
        improvements.append("Resume may be too brief - aim for 400-700 words for 1 page")
    elif word_count < 300:
        issues.append("Resume too short - add more detail about your experience")
    elif 700 < word_count <= 1000:
        score += 10
        improvements.append("Consider condensing content - ideal is 400-700 words per page")
    else:
        issues.append("Resume too long - recruiters spend ~6 seconds on initial scan")
        improvements.append("Condense to 1-2 pages maximum")

    # Check for ATS-unfriendly elements
    ats_issues = []

    # Check for tables (pipes often indicate tables)
    if resume_text.count('|') > 5:
        ats_issues.append("Tables detected - ATS may not parse correctly")

    # Check for multiple columns (indicated by lots of whitespace)
    lines_with_gaps = sum(1 for line in resume_text.split('\n') if '   ' in line)
    if lines_with_gaps > 5:
        ats_issues.append("Multiple columns detected - may confuse ATS parsers")

    # Check for special characters that confuse ATS
    special_chars = ['→', '←', '★', '●', '◆', '▪', '►']
    found_special = [c for c in special_chars if c in resume_text]
    if found_special:
        improvements.append("Replace fancy bullet points with standard ones (•, -, *)")

    if ats_issues:
        issues.extend(ats_issues)
        score -= len(ats_issues) * 5

    # Check for consistent bullet points
    bullet_types = {
        'bullet': len(re.findall(r'•', resume_text)),
        'circle': len(re.findall(r'◦', resume_text)),
        'dash': len(re.findall(r'^\s*[-]\s', resume_text, re.MULTILINE)),
        'asterisk': len(re.findall(r'^\s*[*]\s', resume_text, re.MULTILINE)),
    }

    used_bullets = [k for k, v in bullet_types.items() if v > 0]
    total_bullets = sum(bullet_types.values())

    if len(used_bullets) > 1:
        issues.append("Inconsistent bullet styles - use one type throughout")
    elif total_bullets > 0:
        score += 10
    else:
        improvements.append("Use bullet points to highlight achievements")

    # Check for section headers
    essential_sections = ['experience', 'education', 'skills']
    recommended_sections = ['summary', 'projects', 'certifications']

    found_essential = sum(1 for s in essential_sections if s in resume_text.lower())
    found_recommended = sum(1 for s in recommended_sections if s in resume_text.lower())

    if found_essential == 3:
        score += 15
    elif found_essential >= 2:
        score += 10
        missing = [s for s in essential_sections if s not in resume_text.lower()]
        if missing:
            issues.append(f"Missing essential section: {missing[0].title()}")
    else:
        issues.append("Missing multiple essential sections (Experience, Education, Skills)")

    if found_recommended >= 1:
        score += 5
    else:
        improvements.append("Add recommended sections like Summary, Projects, or Certifications")

    # Check for consistent date formatting
    date_formats = [
        len(re.findall(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', resume_text)),
        len(re.findall(r'\d{1,2}/\d{4}', resume_text)),
        len(re.findall(r'\d{4}\s*[-–]\s*\d{4}', resume_text)),
    ]
    used_formats = sum(1 for d in date_formats if d > 0)
    if used_formats > 1:
        improvements.append("Use consistent date format throughout (e.g., 'Jan 2020' or '01/2020')")
    elif used_formats == 0:
        improvements.append("Add dates to your experience entries for ATS parsing")

    # Check for contact info at top
    first_200_chars = resume_text[:200].lower()
    has_email_top = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', first_200_chars))
    has_phone_top = bool(re.search(r'[\d\-\(\)\+\s]{10,}', first_200_chars))
    if not (has_email_top or has_phone_top):
        improvements.append("Place contact information at the top of your resume")
    else:
        score += 5

    # Check for spelling indicators (common misspellings)
    common_misspellings = ['recieved', 'acheived', 'occured', 'seperate', 'definately',
                          'occurence', 'managment', 'developement', 'enviroment']
    found_misspellings = [m for m in common_misspellings if m in resume_text.lower()]
    if found_misspellings:
        issues.append(f"Possible spelling errors detected: {', '.join(found_misspellings)}")

    # Ensure we always explain why score isn't 100%
    final_score = max(min(score, 100), 0)
    if final_score < 100 and len(improvements) == 0 and len(issues) == 0:
        improvements.append("Review formatting for consistent styling and proper ATS optimization")

    return {
        "name": "Formatting & Structure",
        "icon": "layout",
        "score": final_score,
        "improvements": improvements,
        "issues": issues
    }


def analyze_all_sections(resume_text: str, job_description: str, jd_skills: list[str]) -> dict:
    """Analyze all resume sections and return scores."""
    sections = [
        analyze_contact_section(resume_text),
        analyze_summary_section(resume_text, job_description),
        analyze_experience_section(resume_text, job_description),
        analyze_skills_section(resume_text, jd_skills),
        analyze_education_section(resume_text),
        analyze_certifications_section(resume_text, job_description),
        analyze_formatting(resume_text),
    ]

    # Calculate overall score (weighted average)
    # Experience and Skills are most important for job matching
    weights = [0.08, 0.12, 0.30, 0.25, 0.08, 0.08, 0.09]
    overall_score = sum(s["score"] * w for s, w in zip(sections, weights))

    return {
        "overall_score": int(overall_score),
        "sections": sections,
        "total_sections": len(sections),
        "total_improvements": sum(len(s["improvements"]) for s in sections),
        "total_issues": sum(len(s["issues"]) for s in sections)
    }
