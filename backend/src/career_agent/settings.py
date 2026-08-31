from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAREER_AGENT_", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./career-agent.db"
    provider: str = "demo"
    timezone: str = "Asia/Shanghai"
    auto_create_schema: bool = False
    collector_token: str = ""
    model_base_url: str = ""
    model_api_key: str = ""
    model_name: str = ""
    model_config_path: str = ""
    model_timeout_seconds: float = 180


@lru_cache
def get_settings() -> Settings:
    return Settings()
