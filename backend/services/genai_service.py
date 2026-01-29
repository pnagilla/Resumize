"""
GenAI Semantic Service - AI-assisted analysis using Groq (Llama 3.3).

This service is ASSISTIVE ONLY. It does NOT produce the primary score.
It provides:
  - Semantic skill matching (implied skills)
  - Score adjustment (±15 points max)
  - Gap analysis with actionable advice
  - Bullet point rewriting
  - Portfolio positioning advice

Graceful degradation: if GenAI fails, the system still works with NLP-only scores.
"""

import os
import json
from typing import Optional
from groq import Groq
from fastapi import HTTPException


# Prompt when JD is provided
GENAI_PROMPT_WITH_JD = """You are an ATS analysis assistant. An NLP engine has already scored this resume deterministically.

NLP Score: {nlp_score}/100
NLP Breakdown:
- Skill Match: {skill_score}/100 (weight: {skill_weight}%) — {skill_explanation}
- Keyword Match: {keyword_score}/100 (weight: {keyword_weight}%) — {keyword_explanation}
- Experience: {experience_score}/100 (weight: {experience_weight}%) — {experience_explanation}
- Formatting: {formatting_score}/100 (weight: {formatting_weight}%) — {formatting_explanation}

Matched Skills: {matched_skills}
Missing Skills: {missing_skills}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Analyze the resume semantically and provide a JSON response with this EXACT structure:
{{
    "score_adjustment": <integer between -15 and +15>,
    "adjustment_reason": "<1-2 sentences explaining why you're adjusting the NLP score>",
    "semantic_skills": ["<skill implied but not literally stated>", ...],
    "gap_analysis": [
        {{
            "skill": "<missing skill>",
            "importance": "<high|medium|low>",
            "reason": "<why this matters for the role>",
            "suggestion": "<how to address this gap>"
        }}
    ],
    "rewritten_bullets": [
        {{
            "original": "<original bullet from resume>",
            "rewritten": "<ATS-optimized version>",
            "keywords_used": ["<keyword1>", "<keyword2>"]
        }}
    ],
    "positioning_advice": "<2-3 sentences on how to better position for this role>"
}}

Guidelines:
- SCORE ADJUSTMENT: Only adjust if the NLP score misses important semantic context. Positive if resume has implied relevant experience; negative if skills are superficial.
- SEMANTIC SKILLS: List 3-8 skills the candidate likely has based on their experience but didn't explicitly list.
- GAP ANALYSIS: For top 3-5 missing skills, explain importance and how to address.
- REWRITTEN BULLETS: Select 3-5 bullets and rewrite with JD keywords, action verbs, and metrics.
- POSITIONING ADVICE: Practical, specific advice for this role.

Return ONLY the JSON object, no markdown formatting."""

# Prompt when NO JD is provided
GENAI_PROMPT_NO_JD = """You are an ATS analysis assistant. An NLP engine has already scored this resume for general quality.

NLP Score: {nlp_score}/100
NLP Breakdown:
- Skills Present: {skill_score}/100 — {skill_explanation}
- Content Quality: {keyword_score}/100 — {keyword_explanation}
- Experience: {experience_score}/100 — {experience_explanation}
- Formatting: {formatting_score}/100 — {formatting_explanation}

Detected Skills: {matched_skills}

RESUME:
{resume_text}

Analyze the resume and provide a JSON response with this EXACT structure:
{{
    "score_adjustment": <integer between -15 and +15>,
    "adjustment_reason": "<1-2 sentences explaining your adjustment>",
    "semantic_skills": ["<skill implied but not listed>", ...],
    "gap_analysis": [
        {{
            "skill": "<area to improve>",
            "importance": "<high|medium|low>",
            "reason": "<why this matters>",
            "suggestion": "<how to improve>"
        }}
    ],
    "rewritten_bullets": [
        {{
            "original": "<original bullet>",
            "rewritten": "<improved version>",
            "keywords_used": ["<keyword1>", "<keyword2>"]
        }}
    ],
    "positioning_advice": "<2-3 sentences of general career positioning advice>"
}}

Guidelines:
- Evaluate overall ATS-readiness and suggest improvements.
- REWRITTEN BULLETS: Pick 3-5 weakest bullets and improve with action verbs and metrics.
- GAP ANALYSIS: Suggest 3-5 areas to strengthen.

Return ONLY the JSON object, no markdown formatting."""


def run_genai_analysis(
    resume_text: str,
    job_description: str,
    nlp_result: dict
) -> Optional[dict]:
    """
    Run GenAI semantic analysis. Returns structured insights or None on failure.

    Args:
        resume_text: Parsed resume text
        job_description: Job description text (may be empty)
        nlp_result: Output from nlp_service.run_nlp_analysis()

    Returns:
        Dict with score_adjustment, semantic_skills, gap_analysis,
        rewritten_bullets, positioning_advice. Or None on failure.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None  # Graceful degradation — no API key means skip GenAI

    client = Groq(api_key=api_key)
    breakdown = nlp_result["breakdown"]
    has_jd = bool(job_description and job_description.strip())

    # Build prompt
    prompt_vars = {
        "nlp_score": nlp_result["nlp_score"],
        "skill_score": breakdown["skill_match"]["score"],
        "skill_weight": breakdown["skill_match"]["weight"],
        "skill_explanation": breakdown["skill_match"]["explanation"],
        "keyword_score": breakdown["keyword_match"]["score"],
        "keyword_weight": breakdown["keyword_match"]["weight"],
        "keyword_explanation": breakdown["keyword_match"]["explanation"],
        "experience_score": breakdown["experience_alignment"]["score"],
        "experience_weight": breakdown["experience_alignment"]["weight"],
        "experience_explanation": breakdown["experience_alignment"]["explanation"],
        "formatting_score": breakdown["formatting"]["score"],
        "formatting_weight": breakdown["formatting"]["weight"],
        "formatting_explanation": breakdown["formatting"]["explanation"],
        "matched_skills": ", ".join(breakdown["skill_match"]["details"].get("matched", [])) or "None detected",
        "missing_skills": ", ".join(breakdown["skill_match"]["details"].get("missing", [])) or "None",
        "resume_text": resume_text,
    }

    if has_jd:
        prompt_vars["job_description"] = job_description
        prompt = GENAI_PROMPT_WITH_JD.format(**prompt_vars)
    else:
        prompt = GENAI_PROMPT_NO_JD.format(**prompt_vars)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096
        )
        response_text = response.choices[0].message.content

        # Clean markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Enforce adjustment cap in code (not just prompt)
        raw_adjustment = result.get("score_adjustment", 0)
        if not isinstance(raw_adjustment, (int, float)):
            raw_adjustment = 0
        result["score_adjustment"] = max(-15, min(15, int(raw_adjustment)))

        # Ensure all expected fields exist
        result.setdefault("adjustment_reason", "")
        result.setdefault("semantic_skills", [])
        result.setdefault("gap_analysis", [])
        result.setdefault("rewritten_bullets", [])
        result.setdefault("positioning_advice", "")

        return result

    except json.JSONDecodeError:
        return None  # Graceful degradation
    except Exception:
        return None  # Graceful degradation
