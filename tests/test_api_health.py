from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_service_status():
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "HireLens API"


def test_login_page_renders_for_anonymous_user():
    response = TestClient(app).get("/login")

    assert response.status_code == 200
    assert "Welcome back" in response.text
