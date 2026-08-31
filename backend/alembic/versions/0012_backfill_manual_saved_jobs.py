"""Backfill saved state for existing manual job imports."""

from collections.abc import Sequence

from alembic import op

revision: str = "0012_backfill_manual_saved_jobs"
down_revision: str | None = "0011_saved_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE job_postings SET is_saved = true "
        "WHERE source IN ('manual', 'manual_fixture')"
    )


def downgrade() -> None:
    pass
