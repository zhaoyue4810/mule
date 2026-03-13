from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["config"]["interaction_type_count"] == 15


def test_bootstrap_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/app/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bootstrap_stage"] == "phase_2_content_runtime"
    assert len(payload["interaction_types"]) == 15
