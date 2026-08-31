from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from career_agent.common.models import new_id, utc_now
from career_agent.database import Base
from career_agent.workspace.models import WORKSPACE_USER_ID


class ResumeVariant(Base):
    __tablename__ = "resume_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    root_id: Mapped[str] = mapped_column(String(36), index=True)
    previous_revision_id: Mapped[str | None] = mapped_column(
        ForeignKey("resume_variants.id"), nullable=True
    )
    workspace_id: Mapped[str] = mapped_column(String(36), default=WORKSPACE_USER_ID, index=True)
    job_version_id: Mapped[str] = mapped_column(
        ForeignKey("job_versions.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    target_title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    sections: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class InterviewPack(Base):
    __tablename__ = "interview_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String(36), default=WORKSPACE_USER_ID, index=True)
    job_version_id: Mapped[str] = mapped_column(
        ForeignKey("job_versions.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    title: Mapped[str] = mapped_column(String(300))
    questions: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
