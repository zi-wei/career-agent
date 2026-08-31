from fastapi.testclient import TestClient

from career_agent.main import app


def test_health() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "career-agent"}


def test_runtime_status_exposes_capabilities_without_secrets(client) -> None:
    client.app.state.settings.provider = "openai-compatible"
    client.app.state.settings.model_name = "deepseek-chat"
    client.app.state.settings.model_base_url = "https://api.example.com/v1"
    client.app.state.settings.model_api_key = "must-not-leak"
    client.app.state.settings.collector_token = "collector-secret"

    response = client.get("/api/runtime")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "openai-compatible",
        "model": "deepseek-chat",
        "model_configured": True,
        "collector_sync_enabled": True,
    }
    assert "must-not-leak" not in response.text
    assert "collector-secret" not in response.text
