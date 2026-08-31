from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from career_agent.main import create_app
from career_agent.settings import Settings


class CompatibleModelHandler(BaseHTTPRequestHandler):
    authorization_headers: ClassVar[list[str]] = []

    def do_GET(self) -> None:
        type(self).authorization_headers.append(self.headers.get("Authorization", ""))
        self._send({"data": [{"id": "gpt-5.5"}, {"id": "gpt-5.6-sol"}]})

    def do_POST(self) -> None:
        type(self).authorization_headers.append(self.headers.get("Authorization", ""))
        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length))
        assert payload["model"] == "gpt-5.5"
        self._send({"model": "gpt-5.5", "choices": [{"message": {"content": '{"status":"ok"}'}}]})

    def _send(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def compatible_model_server():
    CompatibleModelHandler.authorization_headers = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), CompatibleModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def build_client(tmp_path: Path, config_path: Path) -> TestClient:
    return TestClient(create_app(Settings(
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'model-settings.db').as_posix()}",
        auto_create_schema=True,
        model_config_path=str(config_path),
        model_timeout_seconds=2,
    )))


def test_model_settings_can_list_save_test_and_reload(
    tmp_path: Path,
    compatible_model_server: ThreadingHTTPServer,
) -> None:
    config_path = tmp_path / "model-settings.json"
    base_url = f"http://127.0.0.1:{compatible_model_server.server_port}/v1"
    api_key = "local-model-secret"

    with build_client(tmp_path, config_path) as client:
        initial = client.get("/api/model-settings")
        assert initial.status_code == 200
        assert initial.json()["api_key_configured"] is False

        models = client.post("/api/model-settings/models", json={
            "base_url": base_url,
            "api_key": api_key,
        })
        assert models.status_code == 200
        assert models.json() == {"items": ["gpt-5.5", "gpt-5.6-sol"]}
        assert api_key not in models.text

        saved = client.put("/api/model-settings", json={
            "base_url": base_url,
            "api_key": api_key,
            "model": "gpt-5.5",
        })
        assert saved.status_code == 200
        assert saved.json() == {
            "provider": "openai-compatible",
            "base_url": base_url,
            "model": "gpt-5.5",
            "api_key_configured": True,
        }
        assert api_key not in saved.text

        tested = client.post("/api/model-settings/test", json={
            "base_url": base_url,
            "model": "gpt-5.5",
        })
        assert tested.status_code == 200
        assert tested.json()["status"] == "ok"
        assert tested.json()["model"] == "gpt-5.5"
        assert api_key not in tested.text
        assert client.get("/api/runtime").json()["model"] == "gpt-5.5"

    with build_client(tmp_path, config_path) as restarted:
        persisted = restarted.get("/api/model-settings")
        assert persisted.json()["model"] == "gpt-5.5"
        assert persisted.json()["api_key_configured"] is True
        assert api_key not in persisted.text

    assert CompatibleModelHandler.authorization_headers == [
        f"Bearer {api_key}",
        f"Bearer {api_key}",
    ]


def test_model_settings_rejects_non_local_plain_http(client: TestClient) -> None:
    response = client.post("/api/model-settings/models", json={
        "base_url": "http://10.0.0.8/v1",
        "api_key": "secret",
    })

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_model_base_url"
