"""
Resume optimization result persistence.

Keyed by (resume_id, job_description_id) pair with a unique constraint,
NOT by analysis_id - optimization here is a standalone feature triggered
directly from a resume+job pair (see app/api/routes/optimization.py), not
tied to a specific completed Analysis run. Re-running optimization for
the same pair upserts rather than duplicates, matching the pattern
already used for ResumeExtractionRecord/JobExtractionRecord.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class OptimizationResultRecord(Base):
    __tablename__ = "optimization_results"
    __table_args__ = (
        UniqueConstraint(
            "resume_id", "job_description_id", name="uq_optimization_resume_job"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )