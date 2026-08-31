from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from career_agent.database import get_session
from career_agent.evidence.models import EvidenceItem
from career_agent.evidence.schemas import EvidenceListView, EvidenceView
from career_agent.evidence.service import delete_evidence, list_evidence

router = APIRouter(tags=["evidence"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/api/evidence", response_model=EvidenceListView)
def read_evidence(session: SessionDependency) -> EvidenceListView:
    return EvidenceListView(
        items=[EvidenceView.model_validate(item) for item in list_evidence(session)]
    )


@router.delete("/api/evidence/{evidence_id}", status_code=204)
def remove_evidence(evidence_id: str, session: SessionDependency) -> Response:
    evidence = session.get(EvidenceItem, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_not_found"})
    delete_evidence(session, evidence)
    return Response(status_code=204)
