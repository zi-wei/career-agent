def seed_profile_and_job(client) -> dict[str, object]:
    profile = client.put(
        "/api/workspace/profile",
        json={
            "target_role": "Linux 运维实习生",
            "cities": ["上海"],
            "availability": "每周 5 天",
            "raw_resume": "个人服务器项目",
            "facts": [
                {
                    "kind": "project",
                    "title": "个人服务器",
                    "content": "使用 Docker 部署 Nginx 服务",
                }
            ],
        },
    ).json()
    job = client.post(
        "/api/jobs/paste",
        json={
            "title": "Linux 运维实习生",
            "company": "示例科技",
            "description": "负责 Linux 系统维护, 使用 Docker 和 Nginx 完成服务部署.",
            "city": "上海",
        },
    ).json()
    return {"profile": profile, "job": job}


def test_generation_uses_profile_facts_and_requirement_evidence(client) -> None:
    seeded = seed_profile_and_job(client)

    response = client.post(f"/api/jobs/{seeded['job']['id']}/materials")

    assert response.status_code == 201
    body = response.json()
    fact_id = seeded["profile"]["facts"][0]["id"]
    bullets = body["resume"]["sections"][0]["bullets"]
    assert bullets[0]["text"] == "使用 Docker 部署 Nginx 服务"
    assert bullets[0]["source_refs"] == [f"profile_fact:{fact_id}"]
    assert "100%" not in response.text
    assert len(body["interview_pack"]["questions"]) == 3


def test_material_generation_analyzes_current_job_version(client) -> None:
    seeded = seed_profile_and_job(client)

    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    detail = client.get(f"/api/jobs/{seeded['job']['id']}").json()

    assert [item["label"] for item in detail["requirements"]] == [
        "Linux",
        "Docker",
        "Nginx",
    ]


def test_latest_materials_survive_a_new_request(client) -> None:
    seeded = seed_profile_and_job(client)
    created = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()

    response = client.get(f"/api/jobs/{seeded['job']['id']}/materials/latest")

    assert response.status_code == 200
    assert response.json()["resume"]["id"] == created["resume"]["id"]


def test_regeneration_creates_a_linked_material_revision(client) -> None:
    seeded = seed_profile_and_job(client)
    first = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()

    second = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()
    latest = client.get(f"/api/jobs/{seeded['job']['id']}/materials/latest").json()

    assert second["resume"]["revision"] == 2
    assert second["resume"]["root_id"] == first["resume"]["root_id"]
    assert second["resume"]["previous_revision_id"] == first["resume"]["id"]
    assert second["interview_pack"]["revision"] == 2
    assert latest["resume"]["id"] == second["resume"]["id"]


def test_material_generation_uses_configured_provider(client) -> None:
    seeded = seed_profile_and_job(client)
    client.app.state.settings.provider = "openai-compatible"

    response = client.post(f"/api/jobs/{seeded['job']['id']}/materials")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_not_configured"


def test_generation_run_records_model_and_completion_metadata(client) -> None:
    from sqlalchemy import select

    from career_agent.generation.models import GenerationRun

    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")

    with client.app.state.session_factory() as session:
        run = session.scalar(
            select(GenerationRun).where(GenerationRun.kind == "materials")
        )

    assert run is not None
    assert run.model == "deterministic-demo"
    assert run.duration_ms is not None
    assert run.completed_at is not None
