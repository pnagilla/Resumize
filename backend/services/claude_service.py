"""
Analysis Orchestrator - Coordinates the layered ATS analysis pipeline.

Pipeline:
  1. NLP Analysis (deterministic, fast) → base score
  2. Section Analysis (deterministic) → per-section breakdown
  3. GenAI Analysis (assistive, may fail gracefully) → semantic insights
  4. Score Combiner → final score with confidence
"""

from fastapi import HTTPException
from models.schemas import (
    AnalysisResult, NLPResult, NLPScoreBreakdown, NLPSubScore,
    GenAIResult, GapAnalysisItem, RewrittenBullet,
    CombinedScore, SectionAnalysis, SectionScore
)
from services.nlp_service import run_nlp_analysis
from services.genai_service import run_genai_analysis
from services.score_combiner import combine_scores
from services.section_service import analyze_all_sections


def analyze_resume(resume_text: str, job_description: str = "") -> AnalysisResult:
    """
    Run the full layered ATS analysis pipeline.

    1. NLP layer: deterministic scoring (skill match, keywords, experience, formatting)
    2. Section analysis: per-section breakdown with improvements/issues
    3. GenAI layer: semantic analysis with score adjustment (±15 max)
    4. Combine: merge NLP + GenAI into final score with confidence level
    """
    if not resume_text or not resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is empty")

    has_jd = bool(job_description and job_description.strip())

    # --- Step 1: NLP Analysis (deterministic) ---
    nlp_raw = run_nlp_analysis(resume_text, job_description)

    # --- Step 2: Section Analysis (deterministic) ---
    extracted_skills = nlp_raw.get("extracted_skills", [])
    section_raw = analyze_all_sections(resume_text, job_description, extracted_skills)

    section_analysis = SectionAnalysis(
        overall_score=section_raw["overall_score"],
        sections=[SectionScore(**s) for s in section_raw["sections"]],
        total_sections=section_raw["total_sections"],
        total_improvements=section_raw["total_improvements"],
        total_issues=section_raw["total_issues"]
    )

    # --- Step 3: GenAI Analysis (assistive, graceful degradation) ---
    genai_raw = None
    genai_result = None
    try:
        genai_raw = run_genai_analysis(resume_text, job_description, nlp_raw)
    except Exception:
        pass  # GenAI failure is non-fatal

    if genai_raw:
        # Parse gap analysis items
        gap_items = []
        for item in genai_raw.get("gap_analysis", []):
            if isinstance(item, dict):
                gap_items.append(GapAnalysisItem(
                    skill=item.get("skill", "Unknown"),
                    importance=item.get("importance", "medium"),
                    reason=item.get("reason", ""),
                    suggestion=item.get("suggestion", "")
                ))

        # Parse rewritten bullets
        bullets = []
        for b in genai_raw.get("rewritten_bullets", []):
            if isinstance(b, dict):
                bullets.append(RewrittenBullet(
                    original=b.get("original", ""),
                    rewritten=b.get("rewritten", ""),
                    keywords_used=b.get("keywords_used", [])
                ))

        genai_result = GenAIResult(
            score_adjustment=genai_raw.get("score_adjustment", 0),
            adjustment_reason=genai_raw.get("adjustment_reason", ""),
            semantic_skills=genai_raw.get("semantic_skills", []),
            gap_analysis=gap_items,
            rewritten_bullets=bullets,
            positioning_advice=genai_raw.get("positioning_advice", "")
        )

    # --- Step 4: Combine Scores ---
    combined_raw = combine_scores(nlp_raw, genai_raw)

    combined_score = CombinedScore(
        final_score=combined_raw["final_score"],
        nlp_score=combined_raw["nlp_score"],
        genai_adjustment=combined_raw["genai_adjustment"],
        genai_available=combined_raw["genai_available"],
        confidence=combined_raw["confidence"],
        adjustment_reason=combined_raw["adjustment_reason"]
    )

    # Build NLP result model
    breakdown = nlp_raw["breakdown"]
    nlp_result = NLPResult(
        score=nlp_raw["nlp_score"],
        breakdown=NLPScoreBreakdown(
            skill_match=NLPSubScore(**breakdown["skill_match"]),
            keyword_match=NLPSubScore(**breakdown["keyword_match"]),
            experience_alignment=NLPSubScore(**breakdown["experience_alignment"]),
            formatting=NLPSubScore(**breakdown["formatting"])
        ),
        extracted_skills=nlp_raw.get("extracted_skills", [])
    )

    # Build justification
    if genai_raw and genai_raw.get("adjustment_reason"):
        justification = genai_raw["adjustment_reason"]
    elif has_jd:
        justification = breakdown["skill_match"]["explanation"]
    else:
        justification = "General ATS analysis completed. Add a job description for targeted skill matching."

    # Get missing skills
    missing_skills = breakdown["skill_match"]["details"].get("missing", [])
    if genai_raw and genai_raw.get("gap_analysis"):
        # Add gap skills from GenAI that aren't already in missing
        gap_skills = [g.get("skill", "") for g in genai_raw["gap_analysis"] if isinstance(g, dict)]
        for s in gap_skills:
            if s and s not in missing_skills:
                missing_skills.append(s)

    return AnalysisResult(
        combined_score=combined_score,
        nlp_result=nlp_result,
        genai_result=genai_result,
        section_analysis=section_analysis,
        match_justification=justification,
        missing_skills=missing_skills
    )
