from typing import cast

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from career_agent.evidence.models import EvidenceItem
from career_agent.generation.contracts import PracticeEvaluationInput
from career_agent.generation.models import GenerationRun
from career_agent.generation.provider import GenerationProvider
from career_agent.planning.models import RollingPlan
from career_agent.practice.models import PracticeEvaluation, PracticeSubmission, PracticeTask
from career_agent.practice.schemas import SubmissionInput


def create_tasks_from_plan(session: Session, plan: RollingPlan) -> list[PracticeTask]:
    existing = list(
        session.scalars(
            select(PracticeTask)
            .where(PracticeTask.plan_id == plan.id)
            .order_by(PracticeTask.created_at)
        )
    )
    if existing:
        return existing
    for day in plan.days:
        for task_data in cast(list[dict[str, object]], day["tasks"]):
            requirement_id = task_data.get("requirement_id")
            session.add(
                PracticeTask(
                    plan_id=plan.id,
                    plan_task_id=str(task_data["id"]),
                    job_version_id=plan.job_version_id,
                    requirement_ids=[str(requirement_id)] if requirement_id else [],
                    kind=str(task_data["kind"]),
                    title=str(task_data["title"]),
                    objective=str(task_data["objective"]),
                    instructions=str(task_data["objective"]),
                    acceptance_criteria=[str(task_data["completion_condition"])],
                    deliverables=[
                        str(task_data.get("evidence_requirement", "学习或实训记录"))
                    ],
                    guidance=cast(dict[str, object], task_data.get("guidance") or {}),
                )
            )
    session.commit()
    return list(
        session.scalars(
            select(PracticeTask)
            .where(PracticeTask.plan_id == plan.id)
            .order_by(PracticeTask.created_at)
        )
    )


def list_tasks(session: Session) -> list[PracticeTask]:
    return list(session.scalars(select(PracticeTask).order_by(PracticeTask.created_at.desc())))


def delete_task(session: Session, task: PracticeTask) -> None:
    submission_ids = list(
        session.scalars(
            select(PracticeSubmission.id).where(PracticeSubmission.task_id == task.id)
        )
    )
    if submission_ids:
        session.execute(
            delete(EvidenceItem).where(
                EvidenceItem.source_type == "practice_submission",
                EvidenceItem.source_id.in_(submission_ids),
            )
        )
        session.execute(
            delete(PracticeEvaluation).where(
                PracticeEvaluation.submission_id.in_(submission_ids)
            )
        )
        session.execute(
            delete(PracticeSubmission).where(PracticeSubmission.id.in_(submission_ids))
        )
    session.delete(task)
    session.commit()


def start_task(session: Session, task: PracticeTask) -> PracticeTask:
    if task.status == "pending":
        task.status = "in_progress"
        session.commit()
        session.refresh(task)
    return task


def submit_task(
    session: Session, task: PracticeTask, payload: SubmissionInput
) -> PracticeSubmission:
    if task.status not in {"in_progress", "needs_revision"}:
        raise ValueError("practice_task_not_submittable")
    submission = PracticeSubmission(
        task_id=task.id,
        content=payload.content.strip(),
        artifact_refs=[str(item) for item in payload.artifact_refs],
        report_summary=payload.report_summary.strip(),
    )
    task.status = "submitted"
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission


def evaluate_submission(
    session: Session,
    submission: PracticeSubmission,
    provider: GenerationProvider,
) -> tuple[PracticeEvaluation, EvidenceItem]:
    existing = session.scalar(
        select(PracticeEvaluation).where(
            PracticeEvaluation.submission_id == submission.id
        )
    )
    if existing is not None:
        evidence = session.scalar(
            select(EvidenceItem).where(
                EvidenceItem.source_type == "practice_submission",
                EvidenceItem.source_id == submission.id,
            )
        )
        if evidence is None:
            raise RuntimeError("evaluation_evidence_inconsistent")
        return existing, evidence
    task = session.get(PracticeTask, submission.task_id)
    if task is None:
        raise RuntimeError("practice_task_missing")
    draft = provider.evaluate_submission(
        PracticeEvaluationInput(
            task_title=task.title,
            objective=task.objective,
            acceptance_criteria=task.acceptance_criteria,
            content=submission.content,
            artifact_refs=submission.artifact_refs,
            report_summary=submission.report_summary,
        )
    )
    evaluation = PracticeEvaluation(
        submission_id=submission.id,
        advisory=draft.advisory,
        summary=draft.summary,
        strengths=draft.strengths,
        improvements=draft.improvements,
    )
    evidence = EvidenceItem(
        job_version_id=task.job_version_id,
        requirement_ids=task.requirement_ids,
        source_type="practice_submission",
        source_id=submission.id,
        title=task.title,
        description=submission.report_summary or submission.content[:1000],
        verification_level="self_reported",
    )
    task.status = "completed"
    submission.status = "evaluated"
    session.add_all([
        evaluation,
        evidence,
        GenerationRun(
            kind="practice_evaluation",
            provider=provider.name,
            model=provider.model,
            prompt_version=provider.prompt_version,
            status="succeeded",
            input_references={"submission_id": submission.id, "task_id": task.id},
        ),
    ])
    session.commit()
    session.refresh(evaluation)
    session.refresh(evidence)
    return evaluation, evidence
