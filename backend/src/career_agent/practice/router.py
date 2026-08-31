from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.generation.openai_compatible import ProviderError
from career_agent.generation.provider import build_provider
from career_agent.planning.models import RollingPlan
from career_agent.practice.models import PracticeSubmission, PracticeTask
from career_agent.practice.schemas import (
    EvaluationView,
    PracticeTaskListView,
    PracticeTaskView,
    SubmissionInput,
    SubmissionView,
)
from career_agent.practice.service import (
    create_tasks_from_plan,
    delete_task,
    evaluate_submission,
    list_tasks,
    start_task,
    submit_task,
)

router = APIRouter(tags=["practice"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post(
    "/api/practice/tasks/from-plan/{plan_id}",
    response_model=PracticeTaskListView,
    status_code=201,
)
def materialize_plan_tasks(plan_id: str, session: SessionDependency) -> PracticeTaskListView:
    plan = session.get(RollingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail={"code": "plan_not_found"})
    return PracticeTaskListView(
        items=[PracticeTaskView.model_validate(item) for item in create_tasks_from_plan(session, plan)]
    )


@router.get("/api/practice/tasks", response_model=PracticeTaskListView)
def read_tasks(session: SessionDependency) -> PracticeTaskListView:
    return PracticeTaskListView(
        items=[PracticeTaskView.model_validate(item) for item in list_tasks(session)]
    )


def require_task(session: Session, task_id: str) -> PracticeTask:
    task = session.get(PracticeTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"code": "practice_task_not_found"})
    return task


@router.post("/api/practice/tasks/{task_id}/start", response_model=PracticeTaskView)
def begin_task(task_id: str, session: SessionDependency) -> PracticeTaskView:
    return PracticeTaskView.model_validate(start_task(session, require_task(session, task_id)))


@router.delete("/api/practice/tasks/{task_id}", status_code=204)
def remove_task(task_id: str, session: SessionDependency) -> Response:
    delete_task(session, require_task(session, task_id))
    return Response(status_code=204)


@router.post(
    "/api/practice/tasks/{task_id}/submissions",
    response_model=SubmissionView,
    status_code=201,
)
def create_submission(
    task_id: str, payload: SubmissionInput, session: SessionDependency
) -> SubmissionView:
    try:
        submission = submit_task(session, require_task(session, task_id), payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error
    return SubmissionView.model_validate(submission)


@router.post(
    "/api/practice/submissions/{submission_id}/evaluate",
    response_model=EvaluationView,
    status_code=201,
)
def evaluate(
    submission_id: str, request: Request, session: SessionDependency
) -> EvaluationView:
    submission = session.get(PracticeSubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail={"code": "submission_not_found"})
    try:
        evaluation, _ = evaluate_submission(
            session, submission, build_provider(request.app.state.settings)
        )
    except ProviderError as error:
        raise HTTPException(status_code=503, detail={"code": error.code}) from error
    return EvaluationView.model_validate(evaluation)
