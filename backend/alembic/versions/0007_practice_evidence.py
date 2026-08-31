"""Create practice, submissions, evaluations and evidence."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_practice_evidence"
down_revision: str | None = "0006_collector_sync"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "practice_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("rolling_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_task_id", sa.String(36), nullable=False),
        sa.Column("job_version_id", sa.String(36), sa.ForeignKey("job_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_ids", sa.JSON(), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False),
        sa.Column("deliverables", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("plan_task_id", name="uq_practice_plan_task"),
    )
    op.create_index("ix_practice_tasks_workspace_id", "practice_tasks", ["workspace_id"])
    op.create_index("ix_practice_tasks_plan_id", "practice_tasks", ["plan_id"])
    op.create_index("ix_practice_tasks_job_version_id", "practice_tasks", ["job_version_id"])
    op.create_table(
        "practice_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("practice_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("artifact_refs", sa.JSON(), nullable=False),
        sa.Column("report_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_practice_submissions_task_id", "practice_submissions", ["task_id"])
    op.create_table(
        "practice_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("submission_id", sa.String(36), sa.ForeignKey("practice_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("advisory", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("improvements", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("submission_id", name="uq_evaluation_submission"),
    )
    op.create_index("ix_practice_evaluations_submission_id", "practice_evaluations", ["submission_id"])
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("job_version_id", sa.String(36), sa.ForeignKey("job_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requirement_ids", sa.JSON(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("verification_level", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_type", "source_id", name="uq_evidence_source"),
    )
    op.create_index("ix_evidence_items_workspace_id", "evidence_items", ["workspace_id"])
    op.create_index("ix_evidence_items_job_version_id", "evidence_items", ["job_version_id"])


def downgrade() -> None:
    op.drop_table("evidence_items")
    op.drop_table("practice_evaluations")
    op.drop_table("practice_submissions")
    op.drop_table("practice_tasks")
