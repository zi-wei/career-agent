from copy import deepcopy

from tests.jobs.test_job_import import load_fixture


def test_duplicate_import_is_idempotent(client) -> None:
    payload = load_fixture()

    first = client.post("/api/jobs/import", json=payload)
    second = client.post("/api/jobs/import", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    detail = client.get(f"/api/jobs/{first.json()['id']}").json()
    assert len(detail["versions"]) == 1


def test_changed_description_creates_new_version(client) -> None:
    payload = load_fixture()
    first = client.post("/api/jobs/import", json=payload).json()
    changed = deepcopy(payload)
    changed["job"]["description"] = "负责 Linux、Docker、Nginx 和 Shell 自动化维护."
    changed["job"]["content_hash"] = "content-v2"
    changed["job"]["version_hash"] = "version-v2"

    response = client.post("/api/jobs/import", json=changed)

    assert response.status_code == 201
    detail = client.get(f"/api/jobs/{first['id']}").json()
    assert [version["content_hash"] for version in detail["versions"]] == [
        "content-v1",
        "content-v2",
    ]
