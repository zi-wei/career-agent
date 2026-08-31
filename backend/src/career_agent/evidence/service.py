from sqlalchemy import select
from sqlalchemy.orm import Session

from career_agent.evidence.models import EvidenceItem


def list_evidence(session: Session) -> list[EvidenceItem]:
    return list(session.scalars(select(EvidenceItem).order_by(EvidenceItem.created_at.desc())))


def delete_evidence(session: Session, evidence: EvidenceItem) -> None:
    session.delete(evidence)
    session.commit()
