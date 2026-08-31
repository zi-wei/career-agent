from sqlalchemy import select
from sqlalchemy.orm import Session

from career_agent.applications.models import (
    Application,
    ApplicationFeedback,
    ApplicationStatusHistory,
    FeedbackAdvice,
)
from career_agent.applications.schemas import ApplicationInput, FeedbackInput
from career_agent.generation.contracts import FeedbackAdviceInput
from career_agent.generation.models import GenerationRun
from career_agent.generation.provider import GenerationProvider
from career_agent.jobs.service import get_job
from career_agent.materials.models import ResumeVariant

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "lead": {"planned", "applied", "withdrawn"},
    "planned": {"applied", "withdrawn"},
    "applied": {"contacted", "interview", "rejected", "silent", "withdrawn"},
    "contacted": {"interview", "rejected", "silent", "withdrawn"},
    "interview": {"interview", "offer", "rejected", "silent", "withdrawn"},
    "offer": {"withdrawn"},
    "rejected": set(),
    "silent": {"contacted", "interview", "withdrawn"},
    "withdrawn": set(),
}


def create_application(
    session: Session, payload: ApplicationInput
) -> Application | None:
    job = get_job(session, payload.job_id)
    if job is None:
        return None
    resume = session.get(ResumeVariant, payload.resume_id)
    if resume is None or resume.job_version_id != job.versions[-1].id:
        raise ValueError("application_resume_mismatch")
    application = Application(
        job_id=job.id,
        job_version_id=job.versions[-1].id,
        resume_id=resume.id,
        status="lead",
        channel=payload.channel.strip(),
        notes=payload.notes.strip(),
    )
    application.history.append(ApplicationStatusHistory(status="lead", note="创建线索"))
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def list_applications(session: Session) -> list[Application]:
    return list(session.scalars(select(Application).order_by(Application.updated_at.desc())))


def update_status(
    session: Session, application: Application, status: str, note: str
) -> Application:
    if status not in ALLOWED_TRANSITIONS.get(application.status, set()):
        raise ValueError("invalid_application_transition")
    application.status = status
    application.history.append(ApplicationStatusHistory(status=status, note=note.strip()))
    session.commit()
    session.refresh(application)
    return application


def add_feedback(
    session: Session, application: Application, payload: FeedbackInput
) -> ApplicationFeedback:
    feedback = ApplicationFeedback(
        application_id=application.id,
        stage=payload.stage.strip(),
        outcome=payload.outcome.strip(),
        question=payload.question.strip(),
        recorded_reason=payload.recorded_reason.strip(),
        notes=payload.notes.strip(),
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def create_advice(
    session: Session, application: Application, provider: GenerationProvider
) -> FeedbackAdvice:
    if not application.feedback:
        raise ValueError("feedback_required")
    facts: list[str] = []
    for item in application.feedback:
        facts.extend(
            value for value in (item.recorded_reason, item.question, item.notes) if value
        )
    if not facts:
        facts = [f"阶段: {item.stage}, 结果: {item.outcome}" for item in application.feedback]
    draft = provider.analyze_feedback(
        FeedbackAdviceInput(
            application_status=application.status,
            source_facts=facts,
        )
    )
    advice = FeedbackAdvice(
        application_id=application.id,
        summary=draft.summary,
        source_facts=draft.source_facts,
        next_actions=draft.next_actions,
    )
    session.add_all([
        advice,
        GenerationRun(
            kind="feedback_advice",
            provider=provider.name,
            model=provider.model,
            prompt_version=provider.prompt_version,
            status="succeeded",
            input_references={
                "application_id": application.id,
                "feedback_ids": [item.id for item in application.feedback],
            },
        ),
    ])
    session.commit()
    session.refresh(advice)
    return advice
