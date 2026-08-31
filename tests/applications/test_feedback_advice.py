from tests.applications.test_application_flow import create_application


def test_feedback_advice_uses_recorded_facts_without_unproven_cause(client) -> None:
    application = create_application(client)
    client.post(
        f"/api/applications/{application['id']}/status",
        json={"status": "applied", "note": "已提交"},
    )
    client.post(
        f"/api/applications/{application['id']}/status",
        json={"status": "rejected", "note": "招聘结束"},
    )
    client.post(
        f"/api/applications/{application['id']}/feedback",
        json={
            "stage": "screening",
            "outcome": "rejected",
            "question": "",
            "recorded_reason": "岗位暂停招聘",
            "notes": "HR邮件通知",
        },
    )

    response = client.post(f"/api/applications/{application['id']}/advice")

    assert response.status_code == 201
    assert "岗位暂停招聘" in response.json()["source_facts"]
    assert "能力不足" not in response.json()["summary"]


def test_feedback_advice_requires_recorded_feedback(client) -> None:
    application = create_application(client)

    response = client.post(f"/api/applications/{application['id']}/advice")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "feedback_required"
