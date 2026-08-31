from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from career_agent.common.models import new_id
from career_agent.generation.contracts import PlanGenerationInput, RequirementContext
from career_agent.generation.models import GenerationRun
from career_agent.generation.provider import GenerationProvider
from career_agent.jobs.service import get_job
from career_agent.materials.models import ResumeVariant
from career_agent.planning.models import RollingPlan, StrengtheningSelection
from career_agent.planning.schemas import SelectionUpdate
from career_agent.workspace.models import WORKSPACE_USER_ID


def selection_map(session: Session, requirement_ids: list[str]) -> dict[str, str]:
    if not requirement_ids:
        return {}
    statement = select(StrengtheningSelection).where(
        StrengtheningSelection.workspace_id == WORKSPACE_USER_ID,
        StrengtheningSelection.requirement_id.in_(requirement_ids),
    )
    return {item.requirement_id: item.state for item in session.scalars(statement)}


def update_selections(
    session: Session, job_id: str, payload: SelectionUpdate
) -> list[StrengtheningSelection] | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    current_requirement_ids = {item.id for item in job.versions[-1].requirements}
    requested_ids = {item.requirement_id for item in payload.selections}
    if not requested_ids.issubset(current_requirement_ids):
        raise ValueError("selection_requirement_mismatch")
    for item in payload.selections:
        existing = session.scalar(
            select(StrengtheningSelection).where(
                StrengtheningSelection.workspace_id == WORKSPACE_USER_ID,
                StrengtheningSelection.requirement_id == item.requirement_id,
            )
        )
        if item.state == "unselected":
            if existing is not None:
                session.delete(existing)
            continue
        if existing is None:
            existing = StrengtheningSelection(requirement_id=item.requirement_id, state=item.state)
            session.add(existing)
        else:
            existing.state = item.state
    session.commit()
    statement = select(StrengtheningSelection).where(
        StrengtheningSelection.workspace_id == WORKSPACE_USER_ID,
        StrengtheningSelection.requirement_id.in_(current_requirement_ids),
    )
    return list(session.scalars(statement))


def has_materials(session: Session, job_version_id: str) -> bool:
    count = session.scalar(
        select(func.count(ResumeVariant.id)).where(
            ResumeVariant.job_version_id == job_version_id,
            ResumeVariant.status != "archived",
        )
    )
    return bool(count)


def create_plan(
    session: Session,
    job_id: str,
    timezone: str,
    provider: GenerationProvider,
) -> RollingPlan | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    version = job.versions[-1]
    if not has_materials(session, version.id):
        raise ValueError("materials_required")
    requirement_ids = [item.id for item in version.requirements]
    states = selection_map(session, requirement_ids)
    selected = [item for item in version.requirements if states.get(item.id) == "strengthen"]
    if not selected:
        raise ValueError("strengthening_selection_required")
    latest_revision = session.scalar(
        select(func.max(RollingPlan.revision)).where(RollingPlan.job_version_id == version.id)
    )
    starts_on = datetime.now(ZoneInfo(timezone)).date()
    draft = provider.generate_plan(
        PlanGenerationInput(
            job_title=job.title,
            selected_requirements=[
                RequirementContext(
                    id=item.id,
                    label=item.label,
                    category=item.category,
                    evidence_text=item.evidence_text,
                )
                for item in selected
            ],
        )
    )
    days: list[dict[str, object]] = []
    for day in draft.days:
        tasks: list[dict[str, object]] = []
        for task in day.tasks:
            tasks.append(
                {
                    "id": new_id(),
                    "kind": "learning" if task.kind == "knowledge_drill" else task.kind,
                    "title": task.title,
                    "objective": task.objective,
                    "estimated_minutes": task.estimated_minutes,
                    "completion_condition": task.completion_condition,
                    "evidence_requirement": task.evidence_requirement,
                    "guidance": task.guidance.model_dump(mode="json"),
                    "requirement_id": task.requirement_id,
                    "status": "pending",
                }
            )
        days.append(
            {
                "day_number": day.day_number,
                "date": (starts_on + timedelta(days=day.day_number - 1)).isoformat(),
                "tasks": tasks,
            }
        )
    session.add(
        GenerationRun(
            kind="plan",
            provider=provider.name,
            model=provider.model,
            prompt_version=provider.prompt_version,
            status="succeeded",
            input_references={
                "job_version_id": version.id,
                "requirement_ids": [item.id for item in selected],
            },
        )
    )
    plan = RollingPlan(
        job_version_id=version.id,
        revision=(latest_revision or 0) + 1,
        status="active",
        timezone=timezone,
        starts_on=starts_on,
        days=days,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def get_latest_plan(session: Session, job_id: str) -> RollingPlan | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    return session.scalar(
        select(RollingPlan)
        .where(RollingPlan.job_version_id == job.versions[-1].id)
        .order_by(RollingPlan.revision.desc())
    )
