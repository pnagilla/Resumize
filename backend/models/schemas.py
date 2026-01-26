from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RewrittenBullet(BaseModel):
    original: str
    rewritten: str
    keywords_used: list[str]


# ATS Score Breakdown Models
class SkillMatchScore(BaseModel):
    score: int
    weight: int
    weighted_score: int
    matched_skills: list[str]
    missing_skills: list[str]


class KeywordMatchScore(BaseModel):
    score: int
    weight: int
    weighted_score: int
    matched_count: int
    total_keywords: int


class ExperienceMatchScore(BaseModel):
    score: int
    weight: int
    weighted_score: int
    note: str


class FormattingScore(BaseModel):
    score: int
    weight: int
    weighted_score: int
    warnings: list[str]


class ATSScoreBreakdown(BaseModel):
    skill_match: SkillMatchScore
    keyword_match: KeywordMatchScore
    experience_match: ExperienceMatchScore
    formatting: FormattingScore


class ATSScore(BaseModel):
    final_score: int
    breakdown: ATSScoreBreakdown


# Section Analysis Models
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


class AnalysisResult(BaseModel):
    match_score: int
    match_justification: str
    missing_skills: list[str]
    rewritten_bullets: list[RewrittenBullet]
    ats_score: Optional[ATSScore] = None
    section_analysis: Optional[SectionAnalysis] = None  # New section breakdown


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
