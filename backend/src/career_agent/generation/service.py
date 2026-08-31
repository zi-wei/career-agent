from sqlalchemy.orm import Session

from career_agent.generation.models import GenerationRun
from career_agent.generation.provider import GenerationProvider
from career_agent.jobs.models import JobRequirement, JobVersion


def analyze_job_version(
    session: Session, version: JobVersion, provider: GenerationProvider
) -> list[JobRequirement]:
    if version.requirements:
        return list(version.requirements)
    run = GenerationRun(
        kind="job_analysis",
        provider=provider.name,
        model=provider.model,
        prompt_version=provider.prompt_version,
        status="running",
        input_references={"job_version_id": version.id},
    )
    session.add(run)
    try:
        draft = provider.analyze_job(version.description)
        version.requirements.extend(
            JobRequirement(
                label=item.label,
                category=item.category,
                evidence_text=item.evidence_text,
                ordinal=index,
            )
            for index, item in enumerate(draft.requirements)
        )
        run.status = "succeeded"
        session.commit()
    except Exception:
        run.status = "failed"
        run.error_code = "job_analysis_failed"
        session.commit()
        raise
    return list(version.requirements)
