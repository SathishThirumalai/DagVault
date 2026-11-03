from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_ready_without_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "not configured"}


def test_health_is_independent_of_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_returns_503_when_database_unavailable(test_cost_log):
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_name="examate-rag",
        environment="test",
        cost_log_path=test_cost_log,
        database_url="postgresql://app:app@127.0.0.1:1/rag",
    )
    with TestClient(app) as client:
        response = client.get("/ready")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not ready"
    assert body["database"]
