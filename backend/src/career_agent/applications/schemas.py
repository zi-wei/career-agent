from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ApplicationStatus = Literal[
    "lead", "planned", "applied", "contacted", "interview",
    "offer", "rejected", "silent", "withdrawn"
]


class ApplicationInput(BaseModel):
    job_id: str
    resume_id: str
    channel: str = Field(min_length=1, max_length=100)
    notes: str = Field(default="", max_length=10000)


class StatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str = Field(default="", max_length=5000)


class StatusHistoryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ApplicationStatus
    note: str
    created_at: datetime


class ApplicationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    job_version_id: str
    resume_id: str
    status: ApplicationStatus
    channel: str
    notes: str
    history: list[StatusHistoryView]
    created_at: datetime
    updated_at: datetime


class ApplicationListView(BaseModel):
    items: list[ApplicationView]


class FeedbackInput(BaseModel):
    stage: str = Field(min_length=1, max_length=50)
    outcome: str = Field(min_length=1, max_length=50)
    question: str = Field(default="", max_length=10000)
    recorded_reason: str = Field(default="", max_length=10000)
    notes: str = Field(default="", max_length=10000)


class FeedbackView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    stage: str
    outcome: str
    question: str
    recorded_reason: str
    notes: str
    created_at: datetime


class AdviceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    summary: str
    source_facts: list[str]
    next_actions: list[str]
    created_at: datetime
