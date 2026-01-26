import os
import json
from groq import Groq
from fastapi import HTTPException
from models.schemas import AnalysisResult, RewrittenBullet, ATSScore, ATSScoreBreakdown
from models.schemas import SkillMatchScore, KeywordMatchScore, ExperienceMatchScore, FormattingScore
from models.schemas import SectionAnalysis, SectionScore
from services.ats_service import calculate_ats_score
from services.section_service import analyze_all_sections

ANALYSIS_PROMPT = """You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.

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


def analyze_resume(resume_text: str, job_description: str) -> AnalysisResult:
    """
    Analyze resume against job description using:
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

    prompt = ANALYSIS_PROMPT.format(
        resume_text=resume_text,
        job_description=job_description
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

        # Step 2: Deterministic ATS Scoring
        jd_skills = ai_analysis.get("jd_skills", [])
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

        # Combine AI insights with deterministic scoring
        return AnalysisResult(
            match_score=section_result["overall_score"],  # Use section-based score
            match_justification=ai_analysis.get("match_justification", ""),
            missing_skills=ai_analysis.get("missing_skills", []),
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
