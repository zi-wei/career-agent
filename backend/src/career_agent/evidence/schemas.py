from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_version_id: str | None
    requirement_ids: list[str]
    source_type: str
    source_id: str
    title: str
    description: str
    verification_level: str
    created_at: datetime


class EvidenceListView(BaseModel):
    items: list[EvidenceView]
