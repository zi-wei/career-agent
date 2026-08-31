from tests.practice.test_practice_flow import create_plan


def test_evaluation_creates_advisory_evidence_transactionally(client) -> None:
    plan = create_plan(client)
    task = client.post(f"/api/practice/tasks/from-plan/{plan['id']}").json()["items"][0]
    client.post(f"/api/practice/tasks/{task['id']}/start")
    submission = client.post(
        f"/api/practice/tasks/{task['id']}/submissions",
        json={
            "content": "完成Docker网络排查记录, 包含现象、步骤和结论.",
            "artifact_refs": [],
            "report_summary": "检查了端口映射和容器日志.",
        },
    ).json()

    evaluation = client.post(
        f"/api/practice/submissions/{submission['id']}/evaluate"
    )
    evidence = client.get("/api/evidence")

    assert evaluation.status_code == 201
    assert evaluation.json()["advisory"] is True
    assert evidence.status_code == 200
    assert evidence.json()["items"][0]["source_id"] == submission["id"]
    assert evidence.json()["items"][0]["verification_level"] == "self_reported"


def test_practice_task_is_not_completed_when_submission_is_missing(client) -> None:
    response = client.post("/api/practice/submissions/missing/evaluate")

    assert response.status_code == 404
    assert client.get("/api/evidence").json()["items"] == []


def test_evidence_can_be_deleted_individually(client) -> None:
    plan = create_plan(client)
    task = client.post(f"/api/practice/tasks/from-plan/{plan['id']}").json()["items"][0]
    client.post(f"/api/practice/tasks/{task['id']}/start")
    submission = client.post(
        f"/api/practice/tasks/{task['id']}/submissions",
        json={"content": "完成记录.", "artifact_refs": [], "report_summary": "结果正常."},
    ).json()
    client.post(f"/api/practice/submissions/{submission['id']}/evaluate")
    evidence_id = client.get("/api/evidence").json()["items"][0]["id"]

    response = client.delete(f"/api/evidence/{evidence_id}")

    assert response.status_code == 204
    assert client.get("/api/evidence").json()["items"] == []
