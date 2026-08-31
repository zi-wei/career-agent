from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from career_agent.main import create_app
from career_agent.settings import Settings


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    database_path = tmp_path / "career-agent-test.db"
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{database_path.as_posix()}",
        auto_create_schema=True,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
