from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class RewrittenBullet(BaseModel):
    original: str
    rewritten: str
    keywords_used: list[str]


# --- NLP Score Models (Deterministic) ---

class NLPSubScore(BaseModel):
    score: int
    weight: int
    weighted_score: int
    explanation: str
    details: dict[str, Any]


class NLPScoreBreakdown(BaseModel):
    skill_match: NLPSubScore
    keyword_match: NLPSubScore
    experience_alignment: NLPSubScore
    formatting: NLPSubScore


class NLPResult(BaseModel):
    score: int
    breakdown: NLPScoreBreakdown
    extracted_skills: list[str]


# --- GenAI Models (Assistive) ---

class GapAnalysisItem(BaseModel):
    skill: str
    importance: str  # "high", "medium", "low"
    reason: str
    suggestion: str


class GenAIResult(BaseModel):
    score_adjustment: int
    adjustment_reason: str
    semantic_skills: list[str]
    gap_analysis: list[GapAnalysisItem]
    rewritten_bullets: list[RewrittenBullet]
    positioning_advice: str


# --- Combined Score ---

class CombinedScore(BaseModel):
    final_score: int
    nlp_score: int
    genai_adjustment: int
    genai_available: bool
    confidence: str  # "high", "moderate", "low", "nlp_only"
    adjustment_reason: str


# --- Section Analysis Models ---

class SectionScore(BaseModel):
    name: str
    icon: str
    score: int
    improvements: list[str]
    issues: list[str]


class SectionAnalysis(BaseModel):
    overall_score: int
    sections: list[SectionScore]
    total_sections: int
    total_improvements: int
    total_issues: int


# --- Main Analysis Result ---

class AnalysisResult(BaseModel):
    combined_score: CombinedScore
    nlp_result: NLPResult
    genai_result: Optional[GenAIResult] = None
    section_analysis: Optional[SectionAnalysis] = None
    match_justification: str
    missing_skills: list[str]


class AnalysisResponse(BaseModel):
    id: Optional[int] = None
    filename: str
    job_title: Optional[str] = None
    analysis: AnalysisResult
    created_at: Optional[datetime] = None


class HistoryItem(BaseModel):
    id: int
    filename: str
    job_title: Optional[str]
    match_score: int
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
