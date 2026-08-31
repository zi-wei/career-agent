from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.jobs.models import JobPosting
from career_agent.jobs.schemas import (
    JobBatchActionInput,
    JobBatchActionResult,
    JobClearResult,
    JobDetailView,
    JobImportEnvelope,
    JobListView,
    JobPasteInput,
    JobPostingV1,
    JobRequirementView,
    JobSavedInput,
    JobSummaryView,
    JobVersionView,
)
from career_agent.jobs.service import (
    apply_job_batch_action,
    clear_jobs,
    delete_job,
    get_job,
    list_jobs,
    paste_job,
    set_job_saved,
    upsert_job,
)
from career_agent.planning.service import selection_map

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
SessionDependency = Annotated[Session, Depends(get_session)]


def to_summary(job: JobPosting) -> JobSummaryView:
    current = job.versions[-1]
    return JobSummaryView(
        id=job.id,
        source=job.source,
        source_job_id=job.source_job_id,
        title=job.title,
        company=job.company,
        city=job.city,
        is_saved=job.is_saved,
        current_version=JobVersionView.model_validate(current),
    )


def to_detail(job: JobPosting, states: dict[str, str] | None = None) -> JobDetailView:
    summary = to_summary(job)
    resolved_states = states or {}
    return JobDetailView(
        **summary.model_dump(),
        versions=[JobVersionView.model_validate(version) for version in job.versions],
        requirements=[
            JobRequirementView(
                id=requirement.id,
                label=requirement.label,
                category=requirement.category,
                evidence_text=requirement.evidence_text,
                selection=resolved_states.get(requirement.id, "unselected"),
            )
            for requirement in job.versions[-1].requirements
        ],
    )


@router.get("", response_model=JobListView)
def read_jobs(session: SessionDependency) -> JobListView:
    return JobListView(items=[to_summary(job) for job in list_jobs(session)])


@router.delete("", response_model=JobClearResult)
def delete_jobs(session: SessionDependency) -> JobClearResult:
    return JobClearResult(deleted_count=clear_jobs(session))


@router.post("/batch-actions", response_model=JobBatchActionResult)
def batch_job_actions(
    payload: JobBatchActionInput, session: SessionDependency
) -> JobBatchActionResult:
    return JobBatchActionResult(
        affected_count=apply_job_batch_action(session, payload.job_ids, payload.action)
    )


@router.put("/{job_id}/saved", response_model=JobDetailView)
def update_job_saved(
    job_id: str, payload: JobSavedInput, session: SessionDependency
) -> JobDetailView:
    job = get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    return to_detail(set_job_saved(session, job, payload.saved))


@router.delete("/{job_id}", status_code=204)
def remove_job(job_id: str, session: SessionDependency) -> Response:
    job = get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    delete_job(session, job)
    return Response(status_code=204)


@router.get("/{job_id}", response_model=JobDetailView)
def read_job(job_id: str, session: SessionDependency) -> JobDetailView:
    job = get_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    requirement_ids = [item.id for item in job.versions[-1].requirements]
    return to_detail(job, selection_map(session, requirement_ids))


@router.post("/import", response_model=JobDetailView)
def import_job(
    envelope: JobImportEnvelope, response: Response, session: SessionDependency
) -> JobDetailView:
    if envelope.payload_schema_version != "1":
        raise HTTPException(status_code=422, detail={"code": "unsupported_job_schema"})
    try:
        payload = JobPostingV1.model_validate(envelope.job)
    except ValidationError as error:
        details = error.errors(include_url=False)
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_job_contract", "fields": details},
        ) from error
    result = upsert_job(session, payload)
    response.status_code = 201 if result.created_version else 200
    job = result.job if result.job.is_saved else set_job_saved(session, result.job, True)
    return to_detail(job)


@router.post("/paste", response_model=JobDetailView)
def create_pasted_job(
    payload: JobPasteInput, response: Response, session: SessionDependency
) -> JobDetailView:
    result = paste_job(session, payload)
    response.status_code = 201 if result.created_version else 200
    return to_detail(result.job)
