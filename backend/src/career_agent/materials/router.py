from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.generation.openai_compatible import ProviderError
from career_agent.generation.provider import build_provider
from career_agent.materials.models import ResumeVariant
from career_agent.materials.renderer import render_resume_markdown
from career_agent.materials.schemas import (
    InterviewPackView,
    MaterialBundleView,
    ResumeRevisionInput,
    ResumeView,
)
from career_agent.materials.service import (
    create_resume_revision,
    generate_materials,
    get_latest_materials,
    get_resume,
    set_resume_status,
)

router = APIRouter(tags=["materials"])
SessionDependency = Annotated[Session, Depends(get_session)]


def require_resume(session: Session, resume_id: str) -> ResumeVariant:
    resume = get_resume(session, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail={"code": "resume_not_found"})
    return resume


@router.post("/api/jobs/{job_id}/materials", response_model=MaterialBundleView, status_code=201)
def create_materials(
    job_id: str, request: Request, session: SessionDependency
) -> MaterialBundleView:
    try:
        provider = build_provider(request.app.state.settings)
        generated = generate_materials(session, job_id, provider)
    except ProviderError as error:
        raise HTTPException(status_code=503, detail={"code": error.code}) from error
    except ValueError as error:
        if str(error) == "unsupported_provider":
            raise HTTPException(status_code=422, detail={"code": str(error)}) from error
        raise
    if generated is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found"})
    job, resume, pack = generated
    return MaterialBundleView(
        job_id=job.id,
        resume=ResumeView.model_validate(resume),
        interview_pack=InterviewPackView.model_validate(pack),
    )


@router.get("/api/jobs/{job_id}/materials/latest", response_model=MaterialBundleView)
def read_latest_materials(job_id: str, session: SessionDependency) -> MaterialBundleView:
    materials = get_latest_materials(session, job_id)
    if materials is None:
        raise HTTPException(status_code=404, detail={"code": "materials_not_found"})
    job, resume, pack = materials
    return MaterialBundleView(
        job_id=job.id,
        resume=ResumeView.model_validate(resume),
        interview_pack=InterviewPackView.model_validate(pack),
    )


@router.get("/api/materials/resumes/{resume_id}", response_model=ResumeView)
def read_resume(resume_id: str, session: SessionDependency) -> ResumeView:
    return ResumeView.model_validate(require_resume(session, resume_id))


@router.post(
    "/api/materials/resumes/{resume_id}/revisions",
    response_model=ResumeView,
    status_code=201,
)
def revise_resume(
    resume_id: str, payload: ResumeRevisionInput, session: SessionDependency
) -> ResumeView:
    source = require_resume(session, resume_id)
    return ResumeView.model_validate(create_resume_revision(session, source, payload))


@router.post("/api/materials/resumes/{resume_id}/confirm", response_model=ResumeView)
def confirm_resume(resume_id: str, session: SessionDependency) -> ResumeView:
    return ResumeView.model_validate(set_resume_status(session, require_resume(session, resume_id), "confirmed"))


@router.post("/api/materials/resumes/{resume_id}/use", response_model=ResumeView)
def use_resume(resume_id: str, session: SessionDependency) -> ResumeView:
    return ResumeView.model_validate(set_resume_status(session, require_resume(session, resume_id), "used"))


@router.delete("/api/materials/resumes/{resume_id}", status_code=204)
def archive_resume(resume_id: str, session: SessionDependency) -> Response:
    resume = require_resume(session, resume_id)
    if resume.status == "used":
        raise HTTPException(status_code=409, detail={"code": "used_resume_is_immutable"})
    set_resume_status(session, resume, "archived")
    return Response(status_code=204)


@router.get("/api/materials/resumes/{resume_id}/export")
def export_resume(
    resume_id: str,
    session: SessionDependency,
    format: Literal["markdown"] = "markdown",
) -> PlainTextResponse:
    resume = require_resume(session, resume_id)
    return PlainTextResponse(render_resume_markdown(resume), media_type="text/markdown")
