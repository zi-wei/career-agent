from dataclasses import dataclass

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from career_agent.jobs.hashing import manual_source_id, normalize_text, sha256_text
from career_agent.jobs.models import JobPosting, JobVersion
from career_agent.jobs.schemas import JobPasteInput, JobPostingV1


@dataclass(frozen=True)
class UpsertResult:
    job: JobPosting
    created_version: bool
    created_job: bool


def list_jobs(session: Session) -> list[JobPosting]:
    statement = (
        select(JobPosting)
        .options(selectinload(JobPosting.versions).selectinload(JobVersion.requirements))
        .order_by(JobPosting.updated_at.desc())
    )
    return list(session.scalars(statement).unique())


def get_job(session: Session, job_id: str) -> JobPosting | None:
    statement = (
        select(JobPosting)
        .where(JobPosting.id == job_id)
        .options(selectinload(JobPosting.versions).selectinload(JobVersion.requirements))
    )
    return session.scalar(statement)


def clear_jobs(session: Session) -> int:
    deleted_count = session.scalar(select(func.count()).select_from(JobPosting)) or 0
    session.execute(delete(JobPosting))
    session.commit()
    return deleted_count


def set_job_saved(session: Session, job: JobPosting, saved: bool) -> JobPosting:
    job.is_saved = saved
    session.commit()
    return get_job(session, job.id) or job


def delete_job(session: Session, job: JobPosting) -> None:
    session.delete(job)
    session.commit()


def apply_job_batch_action(session: Session, job_ids: list[str], action: str) -> int:
    unique_ids = list(dict.fromkeys(job_ids))
    existing_ids = list(
        session.scalars(select(JobPosting.id).where(JobPosting.id.in_(unique_ids)))
    )
    if action == "delete":
        session.execute(delete(JobPosting).where(JobPosting.id.in_(existing_ids)))
    else:
        session.execute(
            update(JobPosting)
            .where(JobPosting.id.in_(existing_ids))
            .values(is_saved=action == "save")
        )
    session.commit()
    return len(existing_ids)


def upsert_job(session: Session, payload: JobPostingV1) -> UpsertResult:
    statement = (
        select(JobPosting)
        .where(
            JobPosting.source == payload.source,
            JobPosting.source_job_id == payload.source_job_id,
        )
        .options(selectinload(JobPosting.versions).selectinload(JobVersion.requirements))
    )
    job = session.scalar(statement)
    created_job = job is None
    if job is None:
        job = JobPosting(
            source=payload.source,
            source_job_id=payload.source_job_id,
            title=normalize_text(payload.title),
            company=normalize_text(payload.company),
            city=normalize_text(payload.city) if payload.city else None,
            is_saved=payload.source == "manual",
        )
        session.add(job)
        session.flush()
    existing = next(
        (version for version in job.versions if version.content_hash == payload.content_hash),
        None,
    )
    if existing is not None:
        return UpsertResult(job=job, created_version=False, created_job=created_job)
    job.title = normalize_text(payload.title)
    job.company = normalize_text(payload.company)
    job.city = normalize_text(payload.city) if payload.city else None
    job.versions.append(
        JobVersion(
            ordinal=len(job.versions) + 1,
            content_hash=payload.content_hash,
            version_hash=payload.version_hash,
            description=normalize_text(payload.description),
            detail_status=payload.detail_status,
            snapshot=payload.model_dump(mode="json"),
        )
    )
    session.commit()
    return UpsertResult(job=get_job(session, job.id) or job, created_version=True, created_job=created_job)


def paste_job(session: Session, payload: JobPasteInput) -> UpsertResult:
    description = normalize_text(payload.description)
    content_hash = sha256_text(description)
    source_id = manual_source_id(payload.company, payload.title)
    imported = JobPostingV1(
        source="manual",
        source_job_id=source_id,
        title=payload.title,
        company=payload.company,
        city=payload.city,
        description=description,
        content_hash=content_hash,
        version_hash=sha256_text(f"{source_id}|{content_hash}"),
        detail_status="complete",
    )
    return upsert_job(session, imported)
