"""Create job requirements and generation runs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_requirements"
down_revision: str | None = "0002_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "job_version_id",
            sa.String(36),
            sa.ForeignKey("job_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("job_version_id", "label", name="uq_job_requirement_label"),
    )
    op.create_index(
        "ix_job_requirements_job_version_id", "job_requirements", ["job_version_id"]
    )
    op.create_table(
        "generation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("input_references", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("generation_runs")
    op.drop_index("ix_job_requirements_job_version_id", table_name="job_requirements")
    op.drop_table("job_requirements")
