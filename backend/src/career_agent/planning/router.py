from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.generation.openai_compatible import ProviderError
from career_agent.generation.provider import build_provider
from career_agent.planning.models import RollingPlan
from career_agent.planning.schemas import (
    RollingPlanView,
    SelectionListView,
    SelectionUpdate,
    SelectionView,
)
from career_agent.planning.service import create_plan, get_latest_plan, update_selections
from career_agent.settings import Settings

router = APIRouter(tags=["planning"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.put("/api/jobs/{job_id}/selections", response_model=SelectionListView)
def write_selections(
    job_id: str, payload: SelectionUpdate, session: SessionDependency
) -> SelectionListView:
    try:
        selections = update_selections(session, job_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": str(error)}) from error
    if selections is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    return SelectionListView(items=[SelectionView.model_validate(item) for item in selections])


@router.post("/api/jobs/{job_id}/plans", response_model=RollingPlanView, status_code=201)
def generate_plan(
    job_id: str, request: Request, session: SessionDependency
) -> RollingPlanView:
    settings: Settings = request.app.state.settings
    try:
        provider = build_provider(settings)
        plan = create_plan(session, job_id, settings.timezone, provider)
    except ProviderError as error:
        raise HTTPException(status_code=503, detail={"code": error.code}) from error
    except ValueError as error:
        if str(error) == "unsupported_provider":
            raise HTTPException(status_code=422, detail={"code": str(error)}) from error
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error
    if plan is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    return RollingPlanView.model_validate(plan)


@router.get("/api/plans/{plan_id}", response_model=RollingPlanView)
def read_plan(plan_id: str, session: SessionDependency) -> RollingPlanView:
    plan = session.get(RollingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail={"code": "plan_not_found"})
    return RollingPlanView.model_validate(plan)


@router.get("/api/jobs/{job_id}/plans/latest", response_model=RollingPlanView)
def read_latest_plan(job_id: str, session: SessionDependency) -> RollingPlanView:
    plan = get_latest_plan(session, job_id)
    if plan is None:
        raise HTTPException(status_code=404, detail={"code": "plan_not_found"})
    return RollingPlanView.model_validate(plan)
