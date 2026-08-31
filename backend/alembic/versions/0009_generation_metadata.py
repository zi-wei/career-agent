"""Add model execution metadata to generation runs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_generation_metadata"
down_revision: str | None = "0008_applications_feedback"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generation_runs", sa.Column("model", sa.String(200), nullable=False, server_default=""))
    op.add_column("generation_runs", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("generation_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("generation_runs", "completed_at")
    op.drop_column("generation_runs", "duration_ms")
    op.drop_column("generation_runs", "model")
