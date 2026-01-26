import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from models.schemas import AnalysisResult, AnalysisResponse, HistoryItem

DATABASE_PATH = "../data/resumize.db"


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
            filename TEXT NOT NULL,
            job_title TEXT,
            job_description TEXT,
            resume_text TEXT,
            match_score INTEGER,
            match_justification TEXT,
            missing_skills TEXT,
            rewritten_bullets TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_analysis(
    filename: str,
    job_description: str,
    resume_text: str,
    analysis: AnalysisResult,
    job_title: Optional[str] = None
) -> int:
    """Save analysis result to database and return the ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analyses (
            filename, job_title, job_description, resume_text,
            match_score, match_justification, missing_skills, rewritten_bullets
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        job_title,
        job_description,
        resume_text,
        analysis.match_score,
        analysis.match_justification,
        json.dumps(analysis.missing_skills),
        json.dumps([b.model_dump() for b in analysis.rewritten_bullets])
    ))

    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return analysis_id


def get_analysis(analysis_id: int) -> Optional[AnalysisResponse]:
    """Retrieve a specific analysis by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return _row_to_response(row)


def get_history(limit: int = 20, offset: int = 0) -> list[HistoryItem]:
    """Get analysis history."""
    conn = get_connection()
    cursor = conn.cursor()

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
    from models.schemas import RewrittenBullet

    missing_skills = json.loads(row["missing_skills"]) if row["missing_skills"] else []
    bullets_data = json.loads(row["rewritten_bullets"]) if row["rewritten_bullets"] else []
    rewritten_bullets = [RewrittenBullet(**b) for b in bullets_data]

    analysis = AnalysisResult(
        match_score=row["match_score"],
        match_justification=row["match_justification"] or "",
        missing_skills=missing_skills,
        rewritten_bullets=rewritten_bullets
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
