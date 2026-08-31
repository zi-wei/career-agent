def test_workspace_profile_is_seeded_and_editable(client) -> None:
    initial = client.get("/api/workspace/profile")

    assert initial.status_code == 200
    assert initial.json()["id"] == "00000000-0000-0000-0000-000000000001"
    assert initial.json()["target_role"] == ""
    assert initial.json()["facts"] == []

    updated = client.put(
        "/api/workspace/profile",
        json={
            "target_role": "Linux 运维实习生",
            "cities": ["上海"],
            "availability": "每周 5 天, 连续 3 个月",
            "raw_resume": "熟悉 Linux 基础命令.",
            "facts": [
                {"kind": "project", "title": "个人服务器", "content": "部署过 Nginx"}
            ],
        },
    )

    assert updated.status_code == 200
    assert updated.json()["target_role"] == "Linux 运维实习生"
    assert updated.json()["facts"][0]["content"] == "部署过 Nginx"


def test_invalid_profile_update_preserves_previous_profile(client) -> None:
    valid_payload = {
        "target_role": "运维实习生",
        "cities": ["杭州"],
        "availability": "每周 4 天",
        "raw_resume": "Linux 项目经历",
        "facts": [{"kind": "skill", "title": "Linux", "content": "完成基础部署"}],
    }
    assert client.put("/api/workspace/profile", json=valid_payload).status_code == 200

    invalid = client.put(
        "/api/workspace/profile",
        json={**valid_payload, "facts": [{"kind": "skill", "title": "", "content": ""}]},
    )

    assert invalid.status_code == 422
    current = client.get("/api/workspace/profile").json()
    assert current["facts"][0]["title"] == "Linux"
