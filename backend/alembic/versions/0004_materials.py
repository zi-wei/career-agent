"""Create resume and interview material tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_materials"
down_revision: str | None = "0003_requirements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("root_id", sa.String(36), nullable=False),
        sa.Column(
            "previous_revision_id",
            sa.String(36),
            sa.ForeignKey("resume_variants.id"),
            nullable=True,
        ),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column(
            "job_version_id",
            sa.String(36),
            sa.ForeignKey("job_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("target_title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resume_variants_root_id", "resume_variants", ["root_id"])
    op.create_index("ix_resume_variants_workspace_id", "resume_variants", ["workspace_id"])
    op.create_index(
        "ix_resume_variants_job_version_id", "resume_variants", ["job_version_id"]
    )
    op.create_table(
        "interview_packs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column(
            "job_version_id",
            sa.String(36),
            sa.ForeignKey("job_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_interview_packs_workspace_id", "interview_packs", ["workspace_id"])
    op.create_index(
        "ix_interview_packs_job_version_id", "interview_packs", ["job_version_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_interview_packs_job_version_id", table_name="interview_packs")
    op.drop_index("ix_interview_packs_workspace_id", table_name="interview_packs")
    op.drop_table("interview_packs")
    op.drop_index("ix_resume_variants_job_version_id", table_name="resume_variants")
    op.drop_index("ix_resume_variants_workspace_id", table_name="resume_variants")
    op.drop_index("ix_resume_variants_root_id", table_name="resume_variants")
    op.drop_table("resume_variants")
