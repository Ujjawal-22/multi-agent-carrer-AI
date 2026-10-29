"""
Request/response schemas for POST /api/analysis and GET /api/analysis/{id}.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.ats_analysis import ATSAnalysisResult
from app.schemas.experience_analysis import ExperienceAnalysisResult
from app.schemas.interview import InterviewPrepResult
from app.schemas.job_extraction import JobExtraction
from app.schemas.matching import MatchingResult
from app.schemas.recommendation import RecommendationResult
from app.schemas.resume_extraction import ResumeExtraction
from app.schemas.skill_gap import SkillGapResult


class AnalysisCreateRequest(BaseModel):
    resume_id: uuid.UUID
    job_description_id: uuid.UUID


class AnalysisErrorDetail(BaseModel):
    agent: str
    message: str


class AnalysisResponse(BaseModel):
    id: uuid.UUID
    status: str
    current_step: str | None = None
    resume_id: uuid.UUID
    job_description_id: uuid.UUID
    created_at: datetime
    completed_at: datetime | None

    resume_extraction: ResumeExtraction | None = None
    jd_extraction: JobExtraction | None = None
    skill_gap_result: SkillGapResult | None = None
    ats_result: ATSAnalysisResult | None = None
    experience_result: ExperienceAnalysisResult | None = None
    matching_result: MatchingResult | None = None
    recommendation_result: RecommendationResult | None = None
    interview_result: InterviewPrepResult | None = None

    # Phase 4 (RAG): which knowledge base source files informed
    # Recommendation/Interview Prep. Currently only populated on the POST
    # response (not yet persisted to the DB), so GET /api/analysis/{id}
    # returns empty lists here for now - a near-term follow-up once this
    # slice is validated, same pattern as the earlier acknowledged
    # resume/job extraction caching follow-up.
    recommendation_sources: list[str] = []
    interview_sources: list[str] = []

    errors: list[AnalysisErrorDetail] = []
