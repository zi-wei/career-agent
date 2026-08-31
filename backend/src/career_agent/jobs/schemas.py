from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class JobPostingV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=50)
    source_job_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    company: str = Field(min_length=1, max_length=300)
    salary_text: str | None = None
    city: str | None = None
    district: str | None = None
    experience: str | None = None
    education: str | None = None
    company_scale: str | None = None
    company_stage: str | None = None
    industry: str | None = None
    recruiter_title: str | None = None
    recruiter_active_status: str | None = None
    skills: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1, max_length=100000)
    source_url: str | None = None
    published_at: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    content_hash: str = Field(min_length=1, max_length=128)
    version_hash: str = Field(min_length=1, max_length=128)
    detail_status: str = Field(min_length=1, max_length=50)
    detail_checked_at: str | None = None
    availability_status: str | None = None
    availability_checked_at: str | None = None
    missing_observation_count: int = 0
    collection_task_id: str | None = None
    field_confidence: dict[str, float] = Field(default_factory=dict)


class JobImportEnvelope(BaseModel):
    payload_schema_version: str
    job: dict[str, Any]


class JobPasteInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    company: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=100000)
    city: str | None = Field(default=None, max_length=100)


class JobVersionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ordinal: int
    content_hash: str
    version_hash: str
    description: str
    detail_status: str
    snapshot: dict[str, Any]


class JobRequirementView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    category: str
    evidence_text: str
    selection: str = "unselected"


class JobSummaryView(BaseModel):
    id: str
    source: str
    source_job_id: str
    title: str
    company: str
    city: str | None
    is_saved: bool
    current_version: JobVersionView


class JobDetailView(JobSummaryView):
    versions: list[JobVersionView]
    requirements: list[JobRequirementView] = Field(default_factory=list)


class JobListView(BaseModel):
    items: list[JobSummaryView]


class JobClearResult(BaseModel):
    deleted_count: int


class JobSavedInput(BaseModel):
    saved: bool


class JobBatchActionInput(BaseModel):
    job_ids: list[str] = Field(min_length=1, max_length=500)
    action: Literal["save", "unsave", "delete"]


class JobBatchActionResult(BaseModel):
    affected_count: int
