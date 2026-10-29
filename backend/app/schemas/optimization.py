"""Pydantic schemas for resume optimization."""

from pydantic import BaseModel, Field


class OptimizationRequest(BaseModel):
    """References to an existing resume and job description."""

    resume_id: str = Field(description="UUID of the uploaded resume")
    job_description_id: str = Field(
        description="UUID of the target job description"
    )


class ResumeSuggestion(BaseModel):
    """One evidence-grounded improvement to the resume."""

    section: str = Field(
        description="Resume section, such as Experience or Projects"
    )
    original_text: str = Field(
        description="Relevant text from the existing resume"
    )
    suggested_text: str = Field(
        description="Improved wording that preserves the candidate's facts"
    )
    reason: str = Field(
        description="Why this change improves relevance or clarity"
    )
    supporting_evidence: str = Field(
        description="Relevant requirement from the supplied job description"
    )
    keywords: list[str] = Field(
        description="Relevant job-description keywords addressed by this change"
    )
    priority: str = Field(
        description="Suggestion priority: high, medium, or low"
    )


class OptimizationResult(BaseModel):
    """Complete structured resume optimization result."""

    summary: str = Field(
        description="Short overview of the most important improvements"
    )
    suggestions: list[ResumeSuggestion] = Field(
        description="Actionable resume improvement suggestions"
    )
    missing_information: list[str] = Field(
        description=(
            "Facts or metrics the candidate could provide to strengthen "
            "the resume; do not invent them"
        )
    )
    warnings: list[str] = Field(
        description="Limitations, unsupported claims, or important caveats"
    )


class OptimizationResponse(BaseModel):
    """API response for resume optimization."""

    resume_id: str
    job_description_id: str
    result: OptimizationResult


# --- ADD THESE TWO NEW CLASSES AT THE BOTTOM ---

class TailoredResumeRequest(BaseModel):
    """Request payload for compiling or refining a tailored resume draft."""

    resume_id: str = Field(description="UUID of the uploaded resume")
    job_description_id: str = Field(
        description="UUID of the target job description"
    )
    selected_suggestion_indices: list[int] = Field(
        default_factory=list,
        description="List of 0-based indices for accepted suggestions",
    )
    custom_instructions: str | None = Field(
        default=None,
        description="Optional custom user prompts or direct tweak instructions",
    )
    version_name: str | None = Field(
        default=None,
        max_length=150,
        description="Optional name for the saved resume version",
    )


class TailoredResumeResponse(BaseModel):
    """API response containing the compiled and saved tailored resume draft."""

    resume_id: str
    job_description_id: str
    tailored_text: str = Field(
        description="Markdown-formatted tailored resume incorporating accepted changes"
    )
    applied_suggestions_count: int = Field(
        description="Total number of suggestions accepted and applied"
    )
    version_id: str = Field(
        description="UUID of the saved resume version"
    )
    version_name: str = Field(
        description="Name assigned to the saved resume version"
    )
    
from datetime import datetime
from uuid import UUID


class ResumeVersionCreate(BaseModel):
    """Payload for saving a tailored resume version."""

    resume_id: UUID
    job_description_id: UUID
    name: str = Field(min_length=1, max_length=150)
    tailored_text: str = Field(min_length=1, max_length=100_000)


class ResumeVersionRename(BaseModel):
    """Payload for renaming a saved resume version."""

    name: str = Field(min_length=1, max_length=150)


class ResumeVersionResponse(BaseModel):
    """Representation of a saved tailored resume version."""

    id: UUID
    resume_id: UUID
    job_description_id: UUID
    name: str
    tailored_text: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeVersionListResponse(BaseModel):
    """Response containing saved versions for a resume and job."""

    versions: list[ResumeVersionResponse]
    total: int
