from tests.materials.test_generation import seed_profile_and_job


def create_application(client) -> dict[str, object]:
    seeded = seed_profile_and_job(client)
    materials = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()
    return client.post(
        "/api/applications",
        json={
            "job_id": seeded["job"]["id"],
            "resume_id": materials["resume"]["id"],
            "channel": "BOSS直聘",
            "notes": "首轮投递",
        },
    ).json()


def test_application_keeps_status_history_and_resume_reference(client) -> None:
    application = create_application(client)

    applied = client.post(
        f"/api/applications/{application['id']}/status",
        json={"status": "applied", "note": "已提交"},
    )
    interview = client.post(
        f"/api/applications/{application['id']}/status",
        json={"status": "interview", "note": "一面"},
    )

    assert applied.status_code == 200
    assert interview.status_code == 200
    assert interview.json()["status"] == "interview"
    assert [item["status"] for item in interview.json()["history"]] == [
        "lead",
        "applied",
        "interview",
    ]
    assert interview.json()["resume_id"] == application["resume_id"]


def test_application_rejects_invalid_status_transition(client) -> None:
    application = create_application(client)

    response = client.post(
        f"/api/applications/{application['id']}/status",
        json={"status": "offer", "note": "跳过全部阶段"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_application_transition"
