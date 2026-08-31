from tests.materials.test_generation import seed_profile_and_job


def test_plan_contains_only_explicit_strengthening_requirements(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    requirements = client.get(f"/api/jobs/{seeded['job']['id']}").json()["requirements"]
    by_label = {item["label"]: item for item in requirements}
    client.put(
        f"/api/jobs/{seeded['job']['id']}/selections",
        json={
            "selections": [
                {"requirement_id": by_label["Docker"]["id"], "state": "strengthen"},
                {"requirement_id": by_label["Nginx"]["id"], "state": "already_have"},
            ]
        },
    )

    response = client.post(f"/api/jobs/{seeded['job']['id']}/plans")

    assert response.status_code == 201
    body = response.json()
    assert len(body["days"]) == 14
    strengthening_tasks = [
        task for day in body["days"] for task in day["tasks"] if task["kind"] == "learning"
    ]
    assert strengthening_tasks
    assert {task["requirement_id"] for task in strengthening_tasks} == {
        by_label["Docker"]["id"]
    }
    assert "缺少" not in response.text


def test_plan_requires_initial_materials(client) -> None:
    seeded = seed_profile_and_job(client)

    response = client.post(f"/api/jobs/{seeded['job']['id']}/plans")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "materials_required"


def test_plan_requires_at_least_one_strengthening_selection(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")

    response = client.post(f"/api/jobs/{seeded['job']['id']}/plans")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "strengthening_selection_required"


def test_latest_plan_survives_a_new_request(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    requirements = client.get(f"/api/jobs/{seeded['job']['id']}").json()["requirements"]
    client.put(
        f"/api/jobs/{seeded['job']['id']}/selections",
        json={
            "selections": [
                {"requirement_id": requirements[0]["id"], "state": "strengthen"}
            ]
        },
    )
    created = client.post(f"/api/jobs/{seeded['job']['id']}/plans").json()

    response = client.get(f"/api/jobs/{seeded['job']['id']}/plans/latest")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_plan_generation_uses_configured_provider(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    requirement = client.get(f"/api/jobs/{seeded['job']['id']}").json()["requirements"][0]
    client.put(
        f"/api/jobs/{seeded['job']['id']}/selections",
        json={"selections": [{"requirement_id": requirement["id"], "state": "strengthen"}]},
    )
    client.app.state.settings.provider = "openai-compatible"

    response = client.post(f"/api/jobs/{seeded['job']['id']}/plans")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_not_configured"
