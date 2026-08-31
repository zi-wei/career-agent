from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from career_agent.collector.schemas import CollectorJobEvent, CollectorSyncAck
from career_agent.collector.service import apply_collector_event
from career_agent.database import get_session

router = APIRouter(prefix="/api/collector-sync/v1", tags=["collector"])
SessionDependency = Annotated[Session, Depends(get_session)]


def require_collector_token(
    request: Request,
    x_collector_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = request.app.state.settings.collector_token
    if not x_collector_token or not expected or not secrets.compare_digest(
        x_collector_token, expected
    ):
        raise HTTPException(status_code=401, detail={"code": "invalid_collector_token"})


@router.post(
    "/jobs",
    response_model=CollectorSyncAck,
    dependencies=[Depends(require_collector_token)],
)
def sync_job(
    event: CollectorJobEvent,
    response: Response,
    session: SessionDependency,
) -> CollectorSyncAck:
    if event.event_schema_version != "1":
        raise HTTPException(status_code=422, detail={"code": "unsupported_event_schema"})
    result = apply_collector_event(session, event)
    response.status_code = 200 if result.replayed else 201
    return result.ack
