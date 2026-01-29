"""
Score Combiner Service - Merges NLP deterministic score with GenAI semantic adjustment.

Final Score = NLP Score + GenAI Adjustment (clamped to ±15, result clamped to 0-100)

Confidence levels:
  - "high": GenAI adjustment ≤ ±5 (NLP and AI agree)
  - "moderate": GenAI adjustment 6-10
  - "low": GenAI adjustment 11-15 or GenAI unavailable
"""

from typing import Optional


def combine_scores(nlp_result: dict, genai_result: Optional[dict]) -> dict:
    """
    Combine NLP deterministic score with GenAI semantic adjustment.

    Args:
        nlp_result: Output from nlp_service.run_nlp_analysis()
        genai_result: Output from genai_service.run_genai_analysis(), or None

    Returns:
        Combined score dict with full breakdown.
    """
    nlp_score = nlp_result["nlp_score"]

    if genai_result:
        raw_adjustment = genai_result.get("score_adjustment", 0)
        adjustment = max(-15, min(15, int(raw_adjustment)))
        adjustment_reason = genai_result.get("adjustment_reason", "")
        genai_available = True
    else:
        adjustment = 0
        adjustment_reason = "AI analysis unavailable. Score based on deterministic NLP analysis only."
        genai_available = False

    final_score = max(0, min(100, nlp_score + adjustment))

    # Determine confidence
    abs_adj = abs(adjustment)
    if not genai_available:
        confidence = "nlp_only"
    elif abs_adj <= 5:
        confidence = "high"
    elif abs_adj <= 10:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "final_score": final_score,
        "nlp_score": nlp_score,
        "genai_adjustment": adjustment,
        "genai_available": genai_available,
        "confidence": confidence,
        "adjustment_reason": adjustment_reason,
        "score_sources": {
            "deterministic": {
                "score": nlp_score,
                "label": "NLP Analysis",
                "description": "Rule-based scoring using skill matching, keyword density, experience alignment, and formatting checks.",
                "breakdown": nlp_result["breakdown"]
            },
            "ai_assisted": {
                "adjustment": adjustment,
                "label": "AI Semantic Adjustment",
                "description": "AI-powered adjustment based on semantic understanding of skills, experience context, and role fit.",
                "reason": adjustment_reason,
                "available": genai_available
            }
        }
    }
