import os
import json
from groq import Groq
from fastapi import HTTPException
from models.schemas import AnalysisResult, RewrittenBullet, ATSScore, ATSScoreBreakdown
from models.schemas import SkillMatchScore, KeywordMatchScore, ExperienceMatchScore, FormattingScore
from models.schemas import SectionAnalysis, SectionScore
from services.ats_service import calculate_ats_score
from services.section_service import analyze_all_sections

# Prompt when job description is provided
ANALYSIS_PROMPT_WITH_JD = """You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.

Analyze the following resume against the job description. Provide a detailed analysis in JSON format.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide your analysis as a valid JSON object with this exact structure:
{{
    "jd_skills": ["<skill1>", "<skill2>", ...],
    "match_justification": "<brief 2-3 sentence explanation of how well the resume matches>",
    "missing_skills": ["<skill1>", "<skill2>", ...],
    "rewritten_bullets": [
        {{
            "original": "<original bullet point from resume>",
            "rewritten": "<ATS-optimized version using JD keywords>",
            "keywords_used": ["<keyword1>", "<keyword2>"]
        }}
    ]
}}

Guidelines:
1. JD_SKILLS: Extract ALL technical skills, tools, frameworks, and qualifications mentioned in the job description
2. MISSING_SKILLS: List specific skills/technologies from the JD not found in the resume
3. REWRITTEN BULLETS: Select 3-5 most relevant bullets and rewrite them to:
   - Start with strong action verbs (Led, Developed, Implemented, Optimized, etc.)
   - Include specific keywords from the job description
   - Add quantifiable achievements where possible
   - Keep each bullet to 1-2 lines
   - Make them ATS-friendly

Return ONLY the JSON object, no additional text or markdown formatting."""

# Prompt when NO job description is provided (general ATS analysis)
ANALYSIS_PROMPT_NO_JD = """You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.

Analyze the following resume for general ATS compatibility and provide improvement suggestions.

RESUME:
{resume_text}

Provide your analysis as a valid JSON object with this exact structure:
{{
    "detected_skills": ["<skill1>", "<skill2>", ...],
    "match_justification": "<2-3 sentence overview of the resume's strengths, weaknesses, and ATS compatibility>",
    "improvement_areas": ["<area1>", "<area2>", ...],
    "rewritten_bullets": [
        {{
            "original": "<original bullet point that could be improved>",
            "rewritten": "<ATS-optimized version with stronger impact>",
            "keywords_used": ["<keyword1>", "<keyword2>"]
        }}
    ]
}}

Guidelines:
1. DETECTED_SKILLS: Extract ALL technical skills, tools, frameworks, soft skills found in the resume
2. IMPROVEMENT_AREAS: List general areas that need improvement (e.g., "Add more quantifiable metrics", "Include LinkedIn profile")
3. REWRITTEN BULLETS: Select 3-5 bullets that could be improved and rewrite them to:
   - Start with strong action verbs (Led, Developed, Implemented, Optimized, etc.)
   - Add quantifiable achievements (%, $, numbers)
   - Make them more impactful and ATS-friendly
   - Keep each bullet to 1-2 lines

Return ONLY the JSON object, no additional text or markdown formatting."""


def analyze_resume(resume_text: str, job_description: str = "") -> AnalysisResult:
    """
    Analyze resume for ATS compatibility.
    If job_description is provided, also performs targeted skill matching.

    Uses:
    - Groq API (Llama 3) for AI insights (bullet rewrites, skill extraction)
    - Deterministic ATS Engine for weighted scoring
    - Section-by-section analysis
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. Please set it in your .env file."
        )

    client = Groq(api_key=api_key)

    # Determine if we have a job description
    has_jd = bool(job_description and job_description.strip())

    if has_jd:
        prompt = ANALYSIS_PROMPT_WITH_JD.format(
            resume_text=resume_text,
            job_description=job_description
        )
    else:
        prompt = ANALYSIS_PROMPT_NO_JD.format(
            resume_text=resume_text
        )

    try:
        # Step 1: AI Analysis (skill extraction, bullet rewrites)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        response_text = response.choices[0].message.content

        # Clean up response if it contains markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON response
        ai_analysis = json.loads(response_text)

        # Get skills list (different key depending on whether JD was provided)
        if has_jd:
            jd_skills = ai_analysis.get("jd_skills", [])
            missing_skills = ai_analysis.get("missing_skills", [])
        else:
            jd_skills = ai_analysis.get("detected_skills", [])
            missing_skills = ai_analysis.get("improvement_areas", [])

        # Step 2: Deterministic ATS Scoring
        ats_result = calculate_ats_score(resume_text, job_description, jd_skills)

        # Build ATS Score breakdown
        breakdown = ats_result["breakdown"]
        ats_score = ATSScore(
            final_score=ats_result["final_score"],
            breakdown=ATSScoreBreakdown(
                skill_match=SkillMatchScore(**breakdown["skill_match"]),
                keyword_match=KeywordMatchScore(**breakdown["keyword_match"]),
                experience_match=ExperienceMatchScore(**breakdown["experience_match"]),
                formatting=FormattingScore(**breakdown["formatting"])
            )
        )

        # Step 3: Section-by-section analysis
        section_result = analyze_all_sections(resume_text, job_description, jd_skills)
        section_analysis = SectionAnalysis(
            overall_score=section_result["overall_score"],
            sections=[SectionScore(**s) for s in section_result["sections"]],
            total_sections=section_result["total_sections"],
            total_improvements=section_result["total_improvements"],
            total_issues=section_result["total_issues"]
        )

        # Convert bullets to Pydantic model
        rewritten_bullets = [
            RewrittenBullet(**bullet)
            for bullet in ai_analysis.get("rewritten_bullets", [])
        ]

        # Build justification message
        if has_jd:
            justification = ai_analysis.get("match_justification", "")
        else:
            justification = ai_analysis.get("match_justification",
                "General ATS analysis completed. Add a job description for targeted skill matching and more specific recommendations.")

        # Combine AI insights with deterministic scoring
        return AnalysisResult(
            match_score=section_result["overall_score"],  # Use section-based score
            match_justification=justification,
            missing_skills=missing_skills,
            rewritten_bullets=rewritten_bullets,
            ats_score=ats_score,
            section_analysis=section_analysis
        )

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
