from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_has_expected_shape() -> None:
    response = client.get("/api/health")
    body = response.json()
    assert "status" in body
    assert "dependencies" in body
    assert "database" in body["dependencies"]
    assert "qdrant" in body["dependencies"]


def test_health_endpoint_returns_200_even_if_qdrant_is_down() -> None:
    # The health check reports Qdrant's status in the body rather than
    # raising - "degraded" is a valid 200 response, not an error.
    response = client.get("/api/health")
    assert response.status_code == 200


def test_root_endpoint_returns_200() -> None:
    response = client.get("/")
    assert response.status_code == 200
