from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from career_agent.common.models import new_id, utc_now
from career_agent.database import Base
from career_agent.workspace.models import WORKSPACE_USER_ID


class StrengtheningSelection(Base):
    __tablename__ = "strengthening_selections"
    __table_args__ = (
        UniqueConstraint("workspace_id", "requirement_id", name="uq_workspace_requirement"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String(36), default=WORKSPACE_USER_ID, index=True)
    requirement_id: Mapped[str] = mapped_column(
        ForeignKey("job_requirements.id", ondelete="CASCADE"), index=True
    )
    state: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class RollingPlan(Base):
    __tablename__ = "rolling_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(String(36), default=WORKSPACE_USER_ID, index=True)
    job_version_id: Mapped[str] = mapped_column(
        ForeignKey("job_versions.id", ondelete="CASCADE"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="active")
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Shanghai")
    starts_on: Mapped[date] = mapped_column(Date)
    days: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
