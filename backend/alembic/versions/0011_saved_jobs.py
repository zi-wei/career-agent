"""Add saved state to job postings."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_saved_jobs"
down_revision: str | None = "0010_practice_guidance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "job_postings",
        sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("job_postings", "is_saved")
