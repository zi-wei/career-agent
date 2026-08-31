"""Create strengthening selections and rolling plans."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_planning"
down_revision: str | None = "0004_materials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strengthening_selections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column(
            "requirement_id",
            sa.String(36),
            sa.ForeignKey("job_requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "requirement_id", name="uq_workspace_requirement"),
    )
    op.create_index(
        "ix_strengthening_selections_workspace_id",
        "strengthening_selections",
        ["workspace_id"],
    )
    op.create_index(
        "ix_strengthening_selections_requirement_id",
        "strengthening_selections",
        ["requirement_id"],
    )
    op.create_table(
        "rolling_plans",
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
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("days", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rolling_plans_workspace_id", "rolling_plans", ["workspace_id"])
    op.create_index("ix_rolling_plans_job_version_id", "rolling_plans", ["job_version_id"])


def downgrade() -> None:
    op.drop_index("ix_rolling_plans_job_version_id", table_name="rolling_plans")
    op.drop_index("ix_rolling_plans_workspace_id", table_name="rolling_plans")
    op.drop_table("rolling_plans")
    op.drop_index(
        "ix_strengthening_selections_requirement_id", table_name="strengthening_selections"
    )
    op.drop_index(
        "ix_strengthening_selections_workspace_id", table_name="strengthening_selections"
    )
    op.drop_table("strengthening_selections")
