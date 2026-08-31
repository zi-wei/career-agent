from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from career_agent.settings import Settings


class ModelSettingsError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def normalize_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    is_allowed = (
        parsed.scheme == "https"
        or (parsed.scheme == "http" and parsed.hostname in local_hosts)
    )
    if (
        not is_allowed
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ModelSettingsError("invalid_model_base_url")
    return normalized


def _resolved_api_key(settings: Settings, candidate: str | None) -> str:
    api_key = candidate.strip() if candidate else settings.model_api_key
    if not api_key:
        raise ModelSettingsError("model_api_key_required")
    return api_key


def load_persisted_model_settings(settings: Settings) -> None:
    if not settings.model_config_path:
        return
    path = Path(settings.model_config_path)
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        base_url = normalize_base_url(str(payload["model_base_url"]))
        api_key = str(payload["model_api_key"]).strip()
        model = str(payload["model_name"]).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ModelSettingsError("invalid_persisted_model_settings") from error
    if not api_key or not model:
        raise ModelSettingsError("invalid_persisted_model_settings")
    settings.provider = "openai-compatible"
    settings.model_base_url = base_url
    settings.model_api_key = api_key
    settings.model_name = model


def save_model_settings(
    settings: Settings,
    base_url: str,
    api_key: str | None,
    model: str,
) -> None:
    normalized_url = normalize_base_url(base_url)
    resolved_key = _resolved_api_key(settings, api_key)
    normalized_model = model.strip()
    if not normalized_model:
        raise ModelSettingsError("model_name_required")

    if settings.model_config_path:
        path = Path(settings.model_config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        payload = {
            "provider": "openai-compatible",
            "model_base_url": normalized_url,
            "model_api_key": resolved_key,
            "model_name": normalized_model,
        }
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
                encoding="utf-8",
            )
            os.chmod(temporary, 0o600)
            temporary.replace(path)
        except OSError as error:
            raise ModelSettingsError("model_settings_write_failed") from error

    settings.provider = "openai-compatible"
    settings.model_base_url = normalized_url
    settings.model_api_key = resolved_key
    settings.model_name = normalized_model


def list_available_models(
    settings: Settings,
    base_url: str,
    api_key: str | None,
) -> list[str]:
    normalized_url = normalize_base_url(base_url)
    resolved_key = _resolved_api_key(settings, api_key)
    response = _request(
        settings,
        "GET",
        f"{normalized_url}/models",
        resolved_key,
    )
    try:
        entries = response.json()["data"]
        model_ids = [entry["id"] for entry in entries]
    except (KeyError, TypeError, ValueError) as error:
        raise ModelSettingsError("invalid_model_response") from error
    if not model_ids or not all(isinstance(model_id, str) and model_id for model_id in model_ids):
        raise ModelSettingsError("invalid_model_response")
    return list(dict.fromkeys(model_ids))


def test_model_connection(
    settings: Settings,
    base_url: str,
    api_key: str | None,
    model: str,
) -> dict[str, str | int]:
    normalized_url = normalize_base_url(base_url)
    resolved_key = _resolved_api_key(settings, api_key)
    normalized_model = model.strip()
    if not normalized_model:
        raise ModelSettingsError("model_name_required")
    started = time.perf_counter()
    response = _request(
        settings,
        "POST",
        f"{normalized_url}/chat/completions",
        resolved_key,
        {
            "model": normalized_model,
            "messages": [
                {"role": "system", "content": "只输出JSON对象."},
                {"role": "user", "content": '返回 {"status":"ok"}.'},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        },
    )
    try:
        content = response.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ModelSettingsError("invalid_model_response") from error
    if not isinstance(result, dict) or result.get("status") != "ok":
        raise ModelSettingsError("invalid_model_response")
    return {
        "status": "ok",
        "model": normalized_model,
        "latency_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }


def _request(
    settings: Settings,
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, object] | None = None,
) -> httpx.Response:
    try:
        with httpx.Client(timeout=settings.model_timeout_seconds) as client:
            response = client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
    except httpx.TransportError as error:
        raise ModelSettingsError("model_service_unreachable") from error
    if response.status_code in {401, 403}:
        raise ModelSettingsError("model_service_auth_failed")
    if response.status_code >= 500:
        raise ModelSettingsError("model_service_unavailable")
    if response.status_code >= 400:
        raise ModelSettingsError("model_service_request_failed")
    return response
