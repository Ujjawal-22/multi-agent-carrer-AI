"""Resume optimization API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.job_description import JobDescription
from app.models.optimization import OptimizationResultRecord
from app.models.resume import Resume
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationResult,
    TailoredResumeRequest,
    TailoredResumeResponse,
)
from app.services.llm.base import LLMGenerationError
from app.services.resume_pdf import generate_resume_pdf
from app.services.optimization_service import optimize_resume
from app.services.tailor import apply_selected_suggestions
from app.models.resume_version import ResumeVersion

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/optimization",
    tags=["optimization"],
)
class ResumePdfRequest(BaseModel):
    tailored_text: str = Field(min_length=1, max_length=100_000)

def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name} UUID.",
        ) from exc


@router.post("", response_model=OptimizationResponse)
def create_optimization(
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
) -> OptimizationResponse:
    """
    Generate resume improvement suggestions for a target job, and persist
    the result. Upserted by (resume_id, job_description_id) - re-running
    optimization for the same pair updates the stored result rather than
    accumulating duplicates, same pattern as resume/job extraction.
    """

    resume_id = _parse_uuid(payload.resume_id, "resume_id")
    job_description_id = _parse_uuid(payload.job_description_id, "job_description_id")

    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {resume_id} not found.",
        )

    job = db.get(JobDescription, job_description_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {job_description_id} not found.",
        )

    if not resume.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected resume contains no text to optimize.",
        )

    if not job.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected job description contains no text.",
        )

    try:
        result = optimize_resume(
            resume_text=resume.raw_text,
            job_description_text=job.raw_text,
        )
    except LLMGenerationError as exc:
        logger.exception("LLM failed to generate resume optimization.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resume optimization could not be generated. Please try again.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected resume optimization failure.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="An unexpected error occurred during resume optimization.",
        ) from exc

    existing = (
        db.query(OptimizationResultRecord)
        .filter_by(resume_id=resume_id, job_description_id=job_description_id)
        .one_or_none()
    )
    if existing is not None:
        existing.data = result.model_dump(mode="json")
    else:
        db.add(
            OptimizationResultRecord(
                id=uuid.uuid4(),
                resume_id=resume_id,
                job_description_id=job_description_id,
                data=result.model_dump(mode="json"),
            )
        )
    db.commit()

    return OptimizationResponse(
        resume_id=str(resume.id),
        job_description_id=str(job.id),
        result=result,
    )

@router.post("/pdf")
def download_resume_pdf(payload: ResumePdfRequest) -> Response:
    """Generate a PDF from a compiled tailored resume."""
    try:
        pdf_bytes = generate_resume_pdf(payload.tailored_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="tailored_resume.pdf"'
        },
    )
@router.get("/{resume_id}/{job_description_id}", response_model=OptimizationResponse)
def get_optimization(
    resume_id: uuid.UUID,
    job_description_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> OptimizationResponse:
    """Retrieve a previously generated optimization result, if one exists."""

    record = (
        db.query(OptimizationResultRecord)
        .filter_by(resume_id=resume_id, job_description_id=job_description_id)
        .one_or_none()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No optimization result found for this resume and job description.",
        )

    return OptimizationResponse(
        resume_id=str(resume_id),
        job_description_id=str(job_description_id),
        result=OptimizationResult.model_validate(record.data),
    )


@router.post("/tailor", response_model=TailoredResumeResponse)
def generate_tailored_resume(
    payload: TailoredResumeRequest,
    db: Session = Depends(get_db),
) -> TailoredResumeResponse:
    """Generate and save a tailored resume version."""

    resume_id = _parse_uuid(payload.resume_id, "resume_id")
    job_description_id = _parse_uuid(
        payload.job_description_id,
        "job_description_id",
    )

    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {resume_id} not found.",
        )

    job = db.get(JobDescription, job_description_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {job_description_id} not found.",
        )

    record = (
        db.query(OptimizationResultRecord)
        .filter_by(
            resume_id=resume_id,
            job_description_id=job_description_id,
        )
        .one_or_none()
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No existing optimization result found. "
                "Run optimization first."
            ),
        )

    opt_result = OptimizationResult.model_validate(record.data)

    tailored_text = apply_selected_suggestions(
        original_resume_text=resume.raw_text,
        optimization_result=opt_result,
        selected_indices=payload.selected_suggestion_indices,
    )

    version_name = (
        payload.version_name.strip()
        if payload.version_name
        else ""
    )

    if not version_name:
        version_name = (
            f"Tailored Resume "
            f"{uuid.uuid4().hex[:8]}"
        )

    version = ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume.id,
        job_description_id=job.id,
        name=version_name,
        tailored_text=tailored_text,
    )

    try:
        db.add(version)
        db.commit()
        db.refresh(version)
    except Exception:
        db.rollback()
        logger.exception("Failed to save tailored resume version.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the tailored resume version.",
        )

    return TailoredResumeResponse(
        resume_id=str(resume_id),
        job_description_id=str(job_description_id),
        tailored_text=tailored_text,
        applied_suggestions_count=len(
            payload.selected_suggestion_indices
        ),
        version_id=str(version.id),
        version_name=version.name,
    )