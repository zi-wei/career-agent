import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from career_agent.common.models import utc_now
from career_agent.generation.contracts import (
    MaterialGenerationInput,
    ProfileFactContext,
    RequirementContext,
)
from career_agent.generation.models import GenerationRun
from career_agent.generation.provider import GenerationProvider
from career_agent.generation.service import analyze_job_version
from career_agent.jobs.models import JobPosting
from career_agent.jobs.service import get_job
from career_agent.materials.models import InterviewPack, ResumeVariant
from career_agent.materials.schemas import ResumeRevisionInput
from career_agent.workspace.models import WORKSPACE_USER_ID
from career_agent.workspace.service import get_workspace


def generate_materials(
    session: Session, job_id: str, provider: GenerationProvider
) -> tuple[JobPosting, ResumeVariant, InterviewPack] | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    version = job.versions[-1]
    profile = get_workspace(session)
    started = time.perf_counter()
    run = GenerationRun(
        kind="materials",
        provider=provider.name,
        model=provider.model,
        prompt_version=provider.prompt_version,
        status="running",
        input_references={
            "job_version_id": version.id,
            "profile_fact_ids": [fact.id for fact in profile.facts],
        },
    )
    session.add(run)
    try:
        requirements = analyze_job_version(session, version, provider)
        draft = provider.generate_materials(MaterialGenerationInput(
            job_title=job.title,
            company=job.company,
            job_description=version.description,
            target_role=profile.target_role or job.title,
            profile_facts=[
                ProfileFactContext(
                    id=fact.id,
                    kind=fact.kind,
                    title=fact.title,
                    content=fact.content,
                )
                for fact in profile.facts
            ],
            requirements=[
                RequirementContext(
                    id=item.id,
                    label=item.label,
                    category=item.category,
                    evidence_text=item.evidence_text,
                )
                for item in requirements
            ],
        ))
        run.status = "succeeded"
    except Exception as error:
        run.status = "failed"
        run.error_code = str(getattr(error, "code", "materials_generation_failed"))
        run.duration_ms = int((time.perf_counter() - started) * 1000)
        run.completed_at = utc_now()
        session.commit()
        raise
    run.duration_ms = int((time.perf_counter() - started) * 1000)
    run.completed_at = utc_now()
    latest_resume = session.scalar(
        select(ResumeVariant)
        .where(
            ResumeVariant.job_version_id == version.id,
            ResumeVariant.status != "archived",
        )
        .order_by(ResumeVariant.revision.desc())
    )
    latest_pack = session.scalar(
        select(InterviewPack)
        .where(InterviewPack.job_version_id == version.id)
        .order_by(InterviewPack.revision.desc())
    )
    resume = ResumeVariant(
        root_id=latest_resume.root_id if latest_resume else "pending",
        previous_revision_id=latest_resume.id if latest_resume else None,
        job_version_id=version.id,
        revision=(latest_resume.revision + 1) if latest_resume else 1,
        status="draft",
        target_title=draft.target_title,
        summary=draft.summary,
        sections=[section.model_dump(mode="json") for section in draft.sections],
    )
    session.add(resume)
    session.flush()
    if latest_resume is None:
        resume.root_id = resume.id
    pack = InterviewPack(
        job_version_id=version.id,
        revision=(latest_pack.revision + 1) if latest_pack else 1,
        status="draft",
        title=draft.interview_title,
        questions=[question.model_dump(mode="json") for question in draft.questions],
    )
    session.add(pack)
    session.commit()
    session.refresh(resume)
    session.refresh(pack)
    return job, resume, pack


def get_resume(session: Session, resume_id: str) -> ResumeVariant | None:
    return session.get(ResumeVariant, resume_id)


def get_latest_materials(
    session: Session, job_id: str
) -> tuple[JobPosting, ResumeVariant, InterviewPack] | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    version_id = job.versions[-1].id
    resume = session.scalar(
        select(ResumeVariant)
        .where(
            ResumeVariant.job_version_id == version_id,
            ResumeVariant.status != "archived",
        )
        .order_by(ResumeVariant.revision.desc())
    )
    pack = session.scalar(
        select(InterviewPack)
        .where(InterviewPack.job_version_id == version_id)
        .order_by(InterviewPack.revision.desc())
    )
    if resume is None or pack is None:
        return None
    return job, resume, pack


def create_resume_revision(
    session: Session, source: ResumeVariant, payload: ResumeRevisionInput
) -> ResumeVariant:
    latest_revision = session.scalar(
        select(func.max(ResumeVariant.revision)).where(ResumeVariant.root_id == source.root_id)
    )
    revision = ResumeVariant(
        root_id=source.root_id,
        previous_revision_id=source.id,
        workspace_id=WORKSPACE_USER_ID,
        job_version_id=source.job_version_id,
        revision=(latest_revision or 0) + 1,
        status="draft",
        target_title=source.target_title,
        summary=payload.summary.strip(),
        sections=[section.model_dump(mode="json") for section in payload.sections],
    )
    session.add(revision)
    session.commit()
    session.refresh(revision)
    return revision


def set_resume_status(session: Session, resume: ResumeVariant, status: str) -> ResumeVariant:
    resume.status = status
    session.commit()
    session.refresh(resume)
    return resume
