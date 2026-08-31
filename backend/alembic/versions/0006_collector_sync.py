"""Create collector event receipts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_collector_sync"
down_revision: str | None = "0005_planning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collector_event_receipts",
        sa.Column("event_id", sa.String(200), primary_key=True),
        sa.Column(
            "job_id",
            sa.String(36),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            sa.String(36),
            sa.ForeignKey("job_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_job", sa.Boolean(), nullable=False),
        sa.Column("created_version", sa.Boolean(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_collector_event_receipts_job_id", "collector_event_receipts", ["job_id"])
    op.create_index(
        "ix_collector_event_receipts_version_id",
        "collector_event_receipts",
        ["version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collector_event_receipts_version_id", table_name="collector_event_receipts"
    )
    op.drop_index("ix_collector_event_receipts_job_id", table_name="collector_event_receipts")
    op.drop_table("collector_event_receipts")
