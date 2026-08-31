from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import select

from career_agent.workspace.models import WORKSPACE_USER_ID, ProfileFact, WorkspaceProfile
from career_agent.workspace.schemas import WorkspaceProfileUpdate


def get_workspace(session: Session) -> WorkspaceProfile:
    statement = (
        select(WorkspaceProfile)
        .where(WorkspaceProfile.id == WORKSPACE_USER_ID)
        .options(selectinload(WorkspaceProfile.facts))
    )
    profile = session.scalar(statement)
    if profile is None:
        profile = WorkspaceProfile(id=WORKSPACE_USER_ID)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def update_workspace(session: Session, payload: WorkspaceProfileUpdate) -> WorkspaceProfile:
    profile = get_workspace(session)
    profile.target_role = payload.target_role.strip()
    profile.cities = [city.strip() for city in payload.cities if city.strip()]
    profile.availability = payload.availability.strip()
    profile.raw_resume = payload.raw_resume.strip()
    profile.facts.clear()
    profile.facts.extend(
        ProfileFact(
            kind=fact.kind.strip(),
            title=fact.title.strip(),
            content=fact.content.strip(),
            ordinal=index,
        )
        for index, fact in enumerate(payload.facts)
    )
    session.commit()
    return get_workspace(session)
