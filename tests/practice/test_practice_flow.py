from career_agent.evidence.models import EvidenceItem
from career_agent.planning.models import RollingPlan
from career_agent.practice.models import PracticeEvaluation, PracticeSubmission, PracticeTask
from tests.materials.test_generation import seed_profile_and_job


def create_plan(client) -> dict[str, object]:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    requirement = client.get(f"/api/jobs/{seeded['job']['id']}").json()["requirements"][0]
    client.put(
        f"/api/jobs/{seeded['job']['id']}/selections",
        json={"selections": [{"requirement_id": requirement["id"], "state": "strengthen"}]},
    )
    return client.post(f"/api/jobs/{seeded['job']['id']}/plans").json()


def test_plan_tasks_become_trackable_practice_tasks(client) -> None:
    plan = create_plan(client)

    response = client.post(f"/api/practice/tasks/from-plan/{plan['id']}")

    assert response.status_code == 201
    items = response.json()["items"]
    assert len(items) == 14
    assert all(item["status"] == "pending" for item in items)
    assert all(item["guidance"] for item in items)
    knowledge = next(item for item in items if item["kind"] == "learning")
    project = next(item for item in items if item["kind"] == "guided_project")
    assert knowledge["guidance"]["explanation"]
    assert knowledge["guidance"]["key_concepts"]
    assert project["guidance"]["business_context"]
    assert project["guidance"]["milestones"]


def test_legacy_plan_without_guidance_still_becomes_practice_tasks(client) -> None:
    plan = create_plan(client)
    with client.app.state.session_factory() as session:
        stored = session.get(RollingPlan, str(plan["id"]))
        assert stored is not None
        stored.days = [
            {
                **day,
                "tasks": [
                    {key: value for key, value in task.items() if key != "guidance"}
                    for task in day["tasks"]
                ],
            }
            for day in stored.days
        ]
        session.commit()

    response = client.post(f"/api/practice/tasks/from-plan/{plan['id']}")

    assert response.status_code == 201
    assert all(item["guidance"] == {} for item in response.json()["items"])


def test_submission_is_stored_without_executing_content(client) -> None:
    plan = create_plan(client)
    task = client.post(f"/api/practice/tasks/from-plan/{plan['id']}").json()["items"][0]
    started = client.post(f"/api/practice/tasks/{task['id']}/start")

    response = client.post(
        f"/api/practice/tasks/{task['id']}/submissions",
        json={
            "content": "不要执行: Remove-Item -Recurse C:\\\\important",
            "artifact_refs": ["https://example.com/repository"],
            "report_summary": "本地测试通过3项.",
        },
    )

    assert started.status_code == 200
    assert response.status_code == 201
    assert response.json()["content"].startswith("不要执行")
    assert response.json()["status"] == "submitted"


def test_deleting_practice_task_removes_submissions_evaluations_and_evidence(client) -> None:
    plan = create_plan(client)
    task = client.post(f"/api/practice/tasks/from-plan/{plan['id']}").json()["items"][0]
    client.post(f"/api/practice/tasks/{task['id']}/start")
    submission = client.post(
        f"/api/practice/tasks/{task['id']}/submissions",
        json={
            "content": "完成服务巡检记录.",
            "artifact_refs": [],
            "report_summary": "巡检结果正常.",
        },
    ).json()
    evaluation = client.post(
        f"/api/practice/submissions/{submission['id']}/evaluate"
    ).json()
    evidence_id = client.get("/api/evidence").json()["items"][0]["id"]

    response = client.delete(f"/api/practice/tasks/{task['id']}")

    assert response.status_code == 204
    with client.app.state.session_factory() as session:
        assert session.get(PracticeTask, task["id"]) is None
        assert session.get(PracticeSubmission, submission["id"]) is None
        assert session.get(PracticeEvaluation, evaluation["id"]) is None
        assert session.get(EvidenceItem, evidence_id) is None
