from tests.materials.test_generation import seed_profile_and_job


def test_requirements_start_unselected(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")

    detail = client.get(f"/api/jobs/{seeded['job']['id']}").json()

    assert {item["selection"] for item in detail["requirements"]} == {"unselected"}


def test_user_can_explicitly_set_each_selection(client) -> None:
    seeded = seed_profile_and_job(client)
    client.post(f"/api/jobs/{seeded['job']['id']}/materials")
    requirements = client.get(f"/api/jobs/{seeded['job']['id']}").json()["requirements"]

    response = client.put(
        f"/api/jobs/{seeded['job']['id']}/selections",
        json={
            "selections": [
                {"requirement_id": requirements[0]["id"], "state": "already_have"},
                {"requirement_id": requirements[1]["id"], "state": "strengthen"},
            ]
        },
    )

    assert response.status_code == 200
    states = {item["requirement_id"]: item["state"] for item in response.json()["items"]}
    assert states[requirements[0]["id"]] == "already_have"
    assert states[requirements[1]["id"]] == "strengthen"
    assert requirements[2]["id"] not in states
