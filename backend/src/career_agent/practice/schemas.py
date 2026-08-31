from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PracticeTaskView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    plan_task_id: str
    job_version_id: str
    requirement_ids: list[str]
    kind: str
    title: str
    objective: str
    instructions: str
    acceptance_criteria: list[str]
    deliverables: list[str]
    guidance: dict[str, object]
    status: str
    updated_at: datetime


class PracticeTaskListView(BaseModel):
    items: list[PracticeTaskView]


class SubmissionInput(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    artifact_refs: list[HttpUrl] = Field(default_factory=list, max_length=20)
    report_summary: str = Field(default="", max_length=10000)


class SubmissionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    content: str
    artifact_refs: list[str]
    report_summary: str
    status: str
    created_at: datetime


class EvaluationView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    advisory: bool
    summary: str
    strengths: list[str]
    improvements: list[str]
    created_at: datetime
