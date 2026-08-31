from pathlib import Path

from career_agent.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_generation_timeouts_cover_long_model_responses() -> None:
    nginx_config = (PROJECT_ROOT / "deploy" / "nginx.conf").read_text(encoding="utf-8")
    compose_config = (PROJECT_ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8")

    assert Settings().model_timeout_seconds >= 180
    assert "CAREER_AGENT_MODEL_TIMEOUT_SECONDS:-180" in compose_config
    assert "proxy_read_timeout 600s;" in nginx_config
