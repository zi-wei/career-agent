from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from career_agent.common.models import new_id, utc_now
from career_agent.database import Base

WORKSPACE_USER_ID = "00000000-0000-0000-0000-000000000001"


class WorkspaceProfile(Base):
    __tablename__ = "workspace_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    target_role: Mapped[str] = mapped_column(String(200), default="")
    cities: Mapped[list[str]] = mapped_column(JSON, default=list)
    availability: Mapped[str] = mapped_column(String(500), default="")
    raw_resume: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    facts: Mapped[list["ProfileFact"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="ProfileFact.ordinal",
    )


class ProfileFact(Base):
    __tablename__ = "profile_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspace_profiles.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer)
    workspace: Mapped[WorkspaceProfile] = relationship(back_populates="facts")
