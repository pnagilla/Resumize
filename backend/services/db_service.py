import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from models.schemas import AnalysisResult, AnalysisResponse, HistoryItem

DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/resumize.db")


def get_connection():
    """Get database connection, creating database if it doesn't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            job_title TEXT,
            job_description TEXT,
            resume_text TEXT,
            match_score INTEGER,
            match_justification TEXT,
            missing_skills TEXT,
            rewritten_bullets TEXT,
            analysis_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add user_id column if it doesn't exist (migration for existing DBs)
    try:
        cursor.execute("ALTER TABLE analyses ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


def save_analysis(
    filename: str,
    job_description: str,
    resume_text: str,
    analysis: AnalysisResult,
    job_title: Optional[str] = None,
    user_id: Optional[int] = None
) -> int:
    """Save analysis result to database and return the ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Store full analysis as JSON for retrieval
    analysis_dict = analysis.model_dump()

    cursor.execute("""
        INSERT INTO analyses (
            user_id, filename, job_title, job_description, resume_text,
            match_score, match_justification, missing_skills, rewritten_bullets, analysis_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        filename,
        job_title,
        job_description,
        resume_text,
        analysis.combined_score.final_score,
        analysis.match_justification,
        json.dumps(analysis.missing_skills),
        json.dumps([b.model_dump() for b in (analysis.genai_result.rewritten_bullets if analysis.genai_result else [])]),
        json.dumps(analysis_dict)
    ))

    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return analysis_id


def get_analysis(analysis_id: int, user_id: Optional[int] = None) -> Optional[AnalysisResponse]:
    """Retrieve a specific analysis by ID, scoped to user if provided."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id))
    else:
        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return _row_to_response(row)


def get_history(limit: int = 20, offset: int = 0, user_id: Optional[int] = None) -> list[HistoryItem]:
    """Get analysis history, scoped to user if provided."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("""
            SELECT id, filename, job_title, match_score, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
    else:
        cursor.execute("""
            SELECT id, filename, job_title, match_score, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    return [
        HistoryItem(
            id=row["id"],
            filename=row["filename"],
            job_title=row["job_title"],
            match_score=row["match_score"],
            created_at=datetime.fromisoformat(row["created_at"])
        )
        for row in rows
    ]


def _row_to_response(row) -> AnalysisResponse:
    """Convert database row to AnalysisResponse."""
    # Try to load full analysis JSON first (new format)
    analysis_json = row["analysis_json"] if "analysis_json" in row.keys() else None

    if analysis_json:
        analysis_data = json.loads(analysis_json)
        analysis = AnalysisResult(**analysis_data)
    else:
        # Fallback for old records without analysis_json
        from models.schemas import CombinedScore, NLPResult, NLPScoreBreakdown, NLPSubScore

        missing_skills = json.loads(row["missing_skills"]) if row["missing_skills"] else []

        # Build minimal compatible response
        empty_sub = NLPSubScore(score=0, weight=25, weighted_score=0, explanation="Legacy record", details={})
        analysis = AnalysisResult(
            combined_score=CombinedScore(
                final_score=row["match_score"] or 0,
                nlp_score=row["match_score"] or 0,
                genai_adjustment=0,
                genai_available=False,
                confidence="nlp_only",
                adjustment_reason="Legacy analysis record"
            ),
            nlp_result=NLPResult(
                score=row["match_score"] or 0,
                breakdown=NLPScoreBreakdown(
                    skill_match=empty_sub,
                    keyword_match=empty_sub,
                    experience_alignment=empty_sub,
                    formatting=empty_sub
                ),
                extracted_skills=[]
            ),
            genai_result=None,
            section_analysis=None,
            match_justification=row["match_justification"] or "",
            missing_skills=missing_skills
        )

    return AnalysisResponse(
        id=row["id"],
        filename=row["filename"],
        job_title=row["job_title"],
        analysis=analysis,
        created_at=datetime.fromisoformat(row["created_at"])
    )


# Initialize database on module load
init_db()
