import json
from pathlib import Path


def load_fixture() -> dict[str, object]:
    path = Path(__file__).parent / "fixtures" / "job_posting_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_import_rejects_unknown_contract_without_partial_write(client) -> None:
    response = client.post(
        "/api/jobs/import",
        json={"payload_schema_version": "99", "job": {"title": "运维实习生"}},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_job_schema"
    assert client.get("/api/jobs").json()["items"] == []


def test_import_requires_complete_contract(client) -> None:
    payload = load_fixture()
    payload["job"].pop("description")  # type: ignore[union-attr]

    response = client.post("/api/jobs/import", json=payload)

    assert response.status_code == 422
    assert client.get("/api/jobs").json()["items"] == []


def test_paste_creates_manual_job_with_generated_hashes(client) -> None:
    response = client.post(
        "/api/jobs/paste",
        json={
            "title": "应用运维实习生",
            "company": "本地示例公司",
            "description": "维护 Linux 系统和 Docker 服务.",
            "city": "杭州",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "manual"
    assert body["current_version"]["content_hash"]


def test_clear_jobs_deletes_every_job_and_reports_count(client) -> None:
    for index in range(2):
        response = client.post(
            "/api/jobs/paste",
            json={
                "title": f"运维实习生 {index}",
                "company": f"示例公司 {index}",
                "description": "负责 Linux 系统维护和故障排查.",
                "city": "临沂",
            },
        )
        assert response.status_code == 201

    response = client.delete("/api/jobs")

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 2}
    assert client.get("/api/jobs").json() == {"items": []}
