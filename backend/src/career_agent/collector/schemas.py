from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from career_agent.jobs.schemas import JobPostingV1


class CollectorJobEvent(BaseModel):
    event_schema_version: str
    event_id: str = Field(min_length=1, max_length=200)
    observed_at: datetime
    job: JobPostingV1


class CollectorSyncAck(BaseModel):
    event_id: str
    job_id: str
    version_id: str
    created_job: bool
    created_version: bool
    replayed: bool
