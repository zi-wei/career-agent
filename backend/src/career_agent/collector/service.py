from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from career_agent.collector.models import CollectorEventReceipt
from career_agent.collector.schemas import CollectorJobEvent, CollectorSyncAck
from career_agent.jobs.service import upsert_job


@dataclass(frozen=True)
class SyncResult:
    ack: CollectorSyncAck
    replayed: bool


def apply_collector_event(session: Session, event: CollectorJobEvent) -> SyncResult:
    existing = session.get(CollectorEventReceipt, event.event_id)
    if existing is not None:
        ack = CollectorSyncAck(
            event_id=existing.event_id,
            job_id=existing.job_id,
            version_id=existing.version_id,
            created_job=existing.created_job,
            created_version=existing.created_version,
            replayed=True,
        )
        return SyncResult(ack=ack, replayed=True)

    result = upsert_job(session, event.job)
    version = result.job.versions[-1]
    receipt = CollectorEventReceipt(
        event_id=event.event_id,
        job_id=result.job.id,
        version_id=version.id,
        created_job=result.created_job,
        created_version=result.created_version,
        observed_at=event.observed_at,
    )
    session.add(receipt)
    session.commit()
    ack = CollectorSyncAck(
        event_id=receipt.event_id,
        job_id=receipt.job_id,
        version_id=receipt.version_id,
        created_job=receipt.created_job,
        created_version=receipt.created_version,
        replayed=False,
    )
    return SyncResult(ack=ack, replayed=False)
