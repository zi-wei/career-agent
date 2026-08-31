from tests.materials.test_generation import seed_profile_and_job


def test_resume_exports_as_markdown(client) -> None:
    seeded = seed_profile_and_job(client)
    resume = client.post(f"/api/jobs/{seeded['job']['id']}/materials").json()["resume"]

    response = client.get(f"/api/materials/resumes/{resume['id']}/export?format=markdown")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# Linux 运维实习生" in response.text
    assert "使用 Docker 部署 Nginx 服务" in response.text
