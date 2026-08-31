from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.workspace.schemas import WorkspaceProfileUpdate, WorkspaceProfileView
from career_agent.workspace.service import get_workspace, update_workspace

router = APIRouter(prefix="/api/workspace", tags=["workspace"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/profile", response_model=WorkspaceProfileView)
def read_profile(session: SessionDependency) -> WorkspaceProfileView:
    return WorkspaceProfileView.model_validate(get_workspace(session))


@router.put("/profile", response_model=WorkspaceProfileView)
def write_profile(
    payload: WorkspaceProfileUpdate, session: SessionDependency
) -> WorkspaceProfileView:
    return WorkspaceProfileView.model_validate(update_workspace(session, payload))
