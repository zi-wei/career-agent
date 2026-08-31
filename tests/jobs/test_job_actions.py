from tests.jobs.test_job_import import load_fixture


def create_manual_job(client, index: int) -> dict[str, object]:
    response = client.post(
        "/api/jobs/paste",
        json={
            "title": f"运维实习生 {index}",
            "company": f"示例公司 {index}",
            "description": "负责 Linux 系统维护和故障排查.",
            "city": "济南",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_manual_paste_and_json_import_are_saved(client) -> None:
    pasted = create_manual_job(client, 1)
    imported = client.post("/api/jobs/import", json=load_fixture())

    assert imported.status_code == 201
    assert pasted["is_saved"] is True
    assert imported.json()["is_saved"] is True


def test_updates_saved_state(client) -> None:
    job = create_manual_job(client, 1)

    response = client.put(f"/api/jobs/{job['id']}/saved", json={"saved": False})

    assert response.status_code == 200
    assert response.json()["is_saved"] is False
    assert client.get(f"/api/jobs/{job['id']}").json()["is_saved"] is False


def test_deletes_one_job_without_deleting_the_rest(client) -> None:
    removed = create_manual_job(client, 1)
    kept = create_manual_job(client, 2)

    response = client.delete(f"/api/jobs/{removed['id']}")

    assert response.status_code == 204
    assert [item["id"] for item in client.get("/api/jobs").json()["items"]] == [kept["id"]]


def test_applies_batch_actions_to_selected_jobs(client) -> None:
    first = create_manual_job(client, 1)
    second = create_manual_job(client, 2)
    third = create_manual_job(client, 3)

    unsaved = client.post(
        "/api/jobs/batch-actions",
        json={"job_ids": [first["id"], second["id"]], "action": "unsave"},
    )
    deleted = client.post(
        "/api/jobs/batch-actions",
        json={"job_ids": [first["id"], second["id"]], "action": "delete"},
    )

    assert unsaved.status_code == 200
    assert unsaved.json() == {"affected_count": 2}
    assert deleted.status_code == 200
    assert deleted.json() == {"affected_count": 2}
    assert [item["id"] for item in client.get("/api/jobs").json()["items"]] == [third["id"]]
