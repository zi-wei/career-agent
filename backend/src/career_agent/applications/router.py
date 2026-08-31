from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from career_agent.applications.models import Application
from career_agent.applications.schemas import (
    AdviceView,
    ApplicationInput,
    ApplicationListView,
    ApplicationView,
    FeedbackInput,
    FeedbackView,
    StatusUpdate,
)
from career_agent.applications.service import (
    add_feedback,
    create_advice,
    create_application,
    list_applications,
    update_status,
)
from career_agent.database import get_session
from career_agent.generation.openai_compatible import ProviderError
from career_agent.generation.provider import build_provider

router = APIRouter(tags=["applications"])
SessionDependency = Annotated[Session, Depends(get_session)]


def require_application(session: Session, application_id: str) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail={"code": "application_not_found"})
    return application


@router.post("/api/applications", response_model=ApplicationView, status_code=201)
def add_application(
    payload: ApplicationInput, session: SessionDependency
) -> ApplicationView:
    try:
        application = create_application(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": str(error)}) from error
    if application is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    return ApplicationView.model_validate(application)


@router.get("/api/applications", response_model=ApplicationListView)
def read_applications(session: SessionDependency) -> ApplicationListView:
    return ApplicationListView(
        items=[ApplicationView.model_validate(item) for item in list_applications(session)]
    )


@router.post("/api/applications/{application_id}/status", response_model=ApplicationView)
def change_status(
    application_id: str, payload: StatusUpdate, session: SessionDependency
) -> ApplicationView:
    try:
        application = update_status(
            session,
            require_application(session, application_id),
            payload.status,
            payload.note,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error
    return ApplicationView.model_validate(application)


@router.post(
    "/api/applications/{application_id}/feedback",
    response_model=FeedbackView,
    status_code=201,
)
def record_feedback(
    application_id: str, payload: FeedbackInput, session: SessionDependency
) -> FeedbackView:
    return FeedbackView.model_validate(
        add_feedback(session, require_application(session, application_id), payload)
    )


@router.post(
    "/api/applications/{application_id}/advice",
    response_model=AdviceView,
    status_code=201,
)
def advise(
    application_id: str, request: Request, session: SessionDependency
) -> AdviceView:
    try:
        advice = create_advice(
            session,
            require_application(session, application_id),
            build_provider(request.app.state.settings),
        )
    except ProviderError as error:
        raise HTTPException(status_code=503, detail={"code": error.code}) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail={"code": str(error)}) from error
    return AdviceView.model_validate(advice)
