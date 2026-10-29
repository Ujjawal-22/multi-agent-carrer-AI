"""
Analysis endpoints.

Phase 5 update: POST /api/analysis now returns IMMEDIATELY (202) and runs
the actual pipeline in a background task (see app/services/analysis_runner.py),
which streams real per-node progress into Analysis.current_step as the
LangGraph pipeline executes. The frontend polls GET /api/analysis/{id}
until status is a terminal value ("completed" or "failed").

This replaces the synchronous "block for 30-60+ seconds" behavior that was
acceptable for early-phase manual testing via Swagger, but not for a real
frontend - a browser request hanging that long risks timeouts and gives
the user zero feedback, which directly conflicts with the spec's required
"Analysis progress" screen.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.analysis import (
    Analysis,
    ATSAnalysisRecord,
    ExperienceAnalysisRecord,
    InterviewQuestionRecord,
    JobExtractionRecord,
    MatchingResultRecord,
    RecommendationRecord,
    ResumeExtractionRecord,
    SkillGapRecord,
)
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.schemas.analysis import AnalysisCreateRequest, AnalysisResponse
from app.schemas.ats_analysis import ATSAnalysisResult
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.schemas.interview import InterviewPrepResult
from app.schemas.job_extraction import JobExtraction
from app.schemas.matching import MatchingResult
from app.schemas.recommendation import RecommendationResult
from app.schemas.resume_extraction import ResumeExtraction
from app.schemas.skill_gap import SkillGapResult
from app.services.analysis_runner import run_analysis_in_background

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
def create_analysis(
    payload: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    resume = db.get(Resume, payload.resume_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume {payload.resume_id} not found.",
        )

    job = db.get(JobDescription, payload.job_description_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description {payload.job_description_id} not found.",
        )

    analysis = Analysis(
        id=uuid.uuid4(),
        resume_id=resume.id,
        job_description_id=job.id,
        status="pending",
        current_step=None,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Capture raw text now, before the request-scoped session closes -
    # the background task opens its own session and shouldn't depend on
    # this one still being open by the time it runs.
    background_tasks.add_task(
        run_analysis_in_background,
        analysis.id,
        resume.raw_text,
        job.raw_text,
    )

    logger.info("Queued analysis %s for background execution", analysis.id)

    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        current_step=analysis.current_step,
        resume_id=analysis.resume_id,
        job_description_id=analysis.job_description_id,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        errors=[],
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisResponse:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found.",
        )

    # Structured results are only persisted once the full pipeline
    # completes (see analysis_runner.py), so while status is "pending" or
    # "running" these will all legitimately be None - the frontend should
    # rely on `current_step` for live progress, not these fields.
    resume_record = (
        db.query(ResumeExtractionRecord)
        .filter_by(resume_id=analysis.resume_id)
        .one_or_none()
    )
    job_record = (
        db.query(JobExtractionRecord)
        .filter_by(job_description_id=analysis.job_description_id)
        .one_or_none()
    )
    skill_gap_record = (
        db.query(SkillGapRecord).filter_by(analysis_id=analysis.id).one_or_none()
    )
    ats_record = (
        db.query(ATSAnalysisRecord).filter_by(analysis_id=analysis.id).one_or_none()
    )
    experience_record = (
        db.query(ExperienceAnalysisRecord)
        .filter_by(analysis_id=analysis.id)
        .one_or_none()
    )
    matching_record = (
        db.query(MatchingResultRecord)
        .filter_by(analysis_id=analysis.id)
        .one_or_none()
    )
    recommendation_record = (
        db.query(RecommendationRecord)
        .filter_by(analysis_id=analysis.id)
        .one_or_none()
    )
    interview_record = (
        db.query(InterviewQuestionRecord)
        .filter_by(analysis_id=analysis.id)
        .one_or_none()
    )

    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        current_step=analysis.current_step,
        resume_id=analysis.resume_id,
        job_description_id=analysis.job_description_id,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        resume_extraction=(
            ResumeExtraction.model_validate(resume_record.data)
            if resume_record
            else None
        ),
        jd_extraction=(
            JobExtraction.model_validate(job_record.data) if job_record else None
        ),
        skill_gap_result=(
            SkillGapResult.model_validate(skill_gap_record.data)
            if skill_gap_record
            else None
        ),
        ats_result=(
            ATSAnalysisResult.model_validate(ats_record.data) if ats_record else None
        ),
        experience_result=(
            ExperienceAnalysisResult.model_validate(experience_record.data)
            if experience_record
            else None
        ),
        matching_result=(
            MatchingResult.model_validate(matching_record.data)
            if matching_record
            else None
        ),
        recommendation_result=(
            RecommendationResult.model_validate(recommendation_record.data)
            if recommendation_record
            else None
        ),
        interview_result=(
            InterviewPrepResult.model_validate(interview_record.data)
            if interview_record
            else None
        ),
        errors=[],
    )
