from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from career_agent.common.models import new_id, utc_now
from career_agent.database import Base
from career_agent.workspace.models import WORKSPACE_USER_ID


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    __table_args__ = (UniqueConstraint("source_type", "source_id", name="uq_evidence_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String(36), default=WORKSPACE_USER_ID, index=True)
    job_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    requirement_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_type: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[str] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    verification_level: Mapped[str] = mapped_column(String(50), default="self_reported")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
