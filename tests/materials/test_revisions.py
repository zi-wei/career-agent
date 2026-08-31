from tests.materials.test_generation import seed_profile_and_job


def test_edit_creates_revision_without_mutating_source(client) -> None:
    seeded = seed_profile_and_job(client)
    generated = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()["resume"]
    sections = generated["sections"]

    edited = client.post(
        f"/api/materials/resumes/{generated['id']}/revisions",
        json={"summary": "面向 Linux 运维岗位", "sections": sections},
    )

    assert edited.status_code == 201
    assert edited.json()["revision"] == generated["revision"] + 1
    original = client.get(f"/api/materials/resumes/{generated['id']}").json()
    assert original["summary"] != edited.json()["summary"]


def test_used_revision_cannot_be_archived(client) -> None:
    seeded = seed_profile_and_job(client)
    generated = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()["resume"]
    assert client.post(f"/api/materials/resumes/{generated['id']}/confirm").status_code == 200
    assert client.post(f"/api/materials/resumes/{generated['id']}/use").status_code == 200

    archived = client.delete(f"/api/materials/resumes/{generated['id']}")

    assert archived.status_code == 409
