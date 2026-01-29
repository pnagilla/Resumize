from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from typing import Optional

from models.schemas import AnalysisResponse, HistoryResponse
from services.parser_service import save_upload_file, parse_resume, cleanup_file
from services.claude_service import analyze_resume
from services.db_service import save_analysis, get_analysis, get_history
from services.auth_service import validate_token

router = APIRouter()


def _get_user(authorization: str = Header(default="")):
    """Extract and validate user from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
    token = authorization[7:]
    user = validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: Optional[str] = Form("", description="Job description text (optional)"),
    job_title: Optional[str] = Form(None, description="Job title (optional)"),
    authorization: str = Header(default="")
):
    """
    Analyze a resume for ATS compatibility and optionally against a job description.

    Requires authentication via Bearer token.
    """
    user = _get_user(authorization)

    # Validate file type
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = resume.filename.lower().split(".")[-1]
    if ext not in ["pdf", "docx", "doc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload PDF or DOCX."
        )

    # Save and parse the resume
    file_path = await save_upload_file(resume)

    try:
        resume_text = parse_resume(file_path)

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume. Please check the file."
            )

        # Analyze with Claude
        analysis = analyze_resume(resume_text, job_description)

        # Save to database
        analysis_id = save_analysis(
            filename=resume.filename,
            job_description=job_description,
            resume_text=resume_text,
            analysis=analysis,
            job_title=job_title,
            user_id=user["id"]
        )

        return AnalysisResponse(
            id=analysis_id,
            filename=resume.filename,
            job_title=job_title,
            analysis=analysis
        )

    finally:
        # Clean up uploaded file
        cleanup_file(file_path)


@router.get("/history", response_model=HistoryResponse)
async def history(
    limit: int = 20,
    offset: int = 0,
    authorization: str = Header(default="")
):
    """
    Get analysis history for the authenticated user.
    """
    user = _get_user(authorization)

    # Bounds validation
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    items = get_history(limit=limit, offset=offset, user_id=user["id"])
    return HistoryResponse(items=items)


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_by_id(
    analysis_id: int,
    authorization: str = Header(default="")
):
    """
    Get a specific analysis by ID. Only returns analyses owned by the authenticated user.
    """
    user = _get_user(authorization)

    result = get_analysis(analysis_id, user_id=user["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
