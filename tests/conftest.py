from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_cost_log(tmp_path: Path) -> str:
    return str(tmp_path / "test_cost.jsonl")


@pytest.fixture
def client(test_cost_log: str):
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_name="examate-rag",
        environment="test",
        cost_log_path=test_cost_log,
        price_input_per_million=1.0,
        price_output_per_million=2.0,
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
