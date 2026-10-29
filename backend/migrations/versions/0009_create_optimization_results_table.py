"""create optimization_results table

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-10

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "optimization_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id"),
            nullable=False,
        ),
        sa.Column(
            "job_description_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_descriptions.id"),
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "resume_id", "job_description_id", name="uq_optimization_resume_job"
        ),
    )


def downgrade() -> None:
    op.drop_table("optimization_results")