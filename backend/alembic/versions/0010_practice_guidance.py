"""Add structured guidance to practice tasks."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_practice_guidance"
down_revision: str | None = "0009_generation_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "practice_tasks",
        sa.Column("guidance", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("practice_tasks", "guidance")
