from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from career_agent.applications import models as application_models  # noqa: F401
from career_agent.applications.router import router as applications_router
from career_agent.collector import models as collector_models  # noqa: F401
from career_agent.collector.router import router as collector_router
from career_agent.database import Base, build_engine, build_session_factory
from career_agent.evidence import models as evidence_models  # noqa: F401
from career_agent.evidence.router import router as evidence_router
from career_agent.generation import models as generation_models  # noqa: F401
from career_agent.generation.model_settings import load_persisted_model_settings
from career_agent.generation.settings_router import router as model_settings_router
from career_agent.jobs import models as job_models  # noqa: F401
from career_agent.jobs.router import router as jobs_router
from career_agent.materials import models as material_models  # noqa: F401
from career_agent.materials.router import router as materials_router
from career_agent.planning import models as planning_models  # noqa: F401
from career_agent.planning.router import router as planning_router
from career_agent.practice import models as practice_models  # noqa: F401
from career_agent.practice.router import router as practice_router
from career_agent.settings import Settings, get_settings
from career_agent.workspace.models import WORKSPACE_USER_ID, WorkspaceProfile
from career_agent.workspace.router import router as workspace_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    load_persisted_model_settings(resolved_settings)
    engine = build_engine(resolved_settings)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if resolved_settings.auto_create_schema:
            Base.metadata.create_all(engine)
        with session_factory() as session:
            if session.get(WorkspaceProfile, WORKSPACE_USER_ID) is None:
                session.add(WorkspaceProfile(id=WORKSPACE_USER_ID))
                session.commit()
        yield
        engine.dispose()

    application = FastAPI(title="Career Agent", version="0.1.0", lifespan=lifespan)
    application.state.settings = resolved_settings
    application.state.session_factory = session_factory
    application.include_router(workspace_router)
    application.include_router(jobs_router)
    application.include_router(materials_router)
    application.include_router(planning_router)
    application.include_router(collector_router)
    application.include_router(practice_router)
    application.include_router(evidence_router)
    application.include_router(applications_router)
    application.include_router(model_settings_router)

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "career-agent"}

    @application.get("/api/runtime")
    def runtime_status() -> dict[str, str | bool]:
        model_configured = bool(
            resolved_settings.model_base_url
            and resolved_settings.model_api_key
            and resolved_settings.model_name
        )
        return {
            "provider": resolved_settings.provider,
            "model": resolved_settings.model_name,
            "model_configured": model_configured,
            "collector_sync_enabled": bool(resolved_settings.collector_token),
        }

    return application


app = create_app()
