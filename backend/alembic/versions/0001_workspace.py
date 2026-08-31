"""Create workspace profile tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_workspace"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("target_role", sa.String(200), nullable=False, server_default=""),
        sa.Column("cities", sa.JSON(), nullable=False),
        sa.Column("availability", sa.String(500), nullable=False, server_default=""),
        sa.Column("raw_resume", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "profile_facts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(36),
            sa.ForeignKey("workspace_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
    )
    op.create_index("ix_profile_facts_workspace_id", "profile_facts", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_profile_facts_workspace_id", table_name="profile_facts")
    op.drop_table("profile_facts")
    op.drop_table("workspace_profiles")
