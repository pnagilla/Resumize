from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from models.schemas import AnalysisResponse, HistoryResponse
from services.parser_service import save_upload_file, parse_resume, cleanup_file
from services.claude_service import analyze_resume
from services.db_service import save_analysis, get_analysis, get_history

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description: Optional[str] = Form("", description="Job description text (optional)"),
    job_title: Optional[str] = Form(None, description="Job title (optional)")
):
    """
    Analyze a resume for ATS compatibility and optionally against a job description.

    - **resume**: Upload your resume (PDF or DOCX format)
    - **job_description**: Paste the job description text (optional - for targeted analysis)
    - **job_title**: Optional job title for reference

    Returns ATS score, section analysis, and improvement suggestions.
    If job description is provided, also returns skill matching and rewritten bullets.
    """
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
            job_title=job_title
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
async def history(limit: int = 20, offset: int = 0):
    """
    Get analysis history.

    - **limit**: Maximum number of items to return (default: 20)
    - **offset**: Number of items to skip (default: 0)
    """
    items = get_history(limit=limit, offset=offset)
    return HistoryResponse(items=items)


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_by_id(analysis_id: int):
    """
    Get a specific analysis by ID.
    """
    result = get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
