from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from career_agent.main import create_app
from career_agent.settings import Settings


@pytest.fixture
def collector_client(tmp_path: Path) -> Iterator[TestClient]:
    database_path = tmp_path / "collector-sync-test.db"
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{database_path.as_posix()}",
        auto_create_schema=True,
        collector_token="test-collector-token",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def event() -> dict[str, object]:
    return {
        "event_schema_version": "1",
        "event_id": "collector-event-001",
        "observed_at": "2026-08-31T00:00:00Z",
        "job": {
            "source": "boss",
            "source_job_id": "boss-job-001",
            "title": "Linux运维实习生",
            "company": "示例科技",
            "salary_text": "150-200元/天",
            "city": "上海",
            "skills": ["Linux", "Docker"],
            "benefits": [],
            "description": "负责 Linux服务器维护、Docker部署和 Nginx配置.",
            "content_hash": "collector-content-v1",
            "version_hash": "collector-version-v1",
            "detail_status": "complete",
            "missing_observation_count": 0,
            "collection_task_id": "task-001",
            "field_confidence": {"title": 1.0, "company": 1.0},
        },
    }


def test_sync_rejects_missing_token_without_partial_write(collector_client) -> None:
    response = collector_client.post("/api/collector-sync/v1/jobs", json=event())

    assert response.status_code == 401
    assert collector_client.get("/api/jobs").json()["items"] == []


def test_sync_creates_job_with_valid_token(collector_client) -> None:
    response = collector_client.post(
        "/api/collector-sync/v1/jobs",
        json=event(),
        headers={"X-Collector-Token": "test-collector-token"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["event_id"] == "collector-event-001"
    assert payload["created_job"] is True
    assert payload["created_version"] is True
    jobs = collector_client.get("/api/jobs").json()["items"]
    assert jobs[0]["source"] == "boss"
    assert jobs[0]["is_saved"] is False


def test_sync_replay_returns_original_ack_without_new_version(collector_client) -> None:
    headers = {"X-Collector-Token": "test-collector-token"}
    first = collector_client.post("/api/collector-sync/v1/jobs", json=event(), headers=headers)
    second = collector_client.post("/api/collector-sync/v1/jobs", json=event(), headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["job_id"] == first.json()["job_id"]
    job = collector_client.get(f"/api/jobs/{first.json()['job_id']}").json()
    assert len(job["versions"]) == 1
