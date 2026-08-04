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


def test_login_rejects_missing_csrf_token():
    response = TestClient(app).post("/login", data={"email": "admin@hirelens.local", "password": "wrong"})

    assert response.status_code == 422


def test_root_redirects_to_dashboard():
    response = TestClient(app).get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/dashboard"


def test_dashboard_redirects_anonymous_user_to_login():
    response = TestClient(app).get("/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_job_rejects_missing_payload():
    response = TestClient(app).post("/api/v1/jobs")

    assert response.status_code == 422


def test_create_job_rejects_negative_experience():
    response = TestClient(app).post("/api/v1/jobs", json={"title": "Engineer", "description": "Build systems", "required_skills": [], "preferred_skills": [], "minimum_years_experience": -1})

    assert response.status_code == 422


def test_create_job_rejects_empty_title():
    response = TestClient(app).post("/api/v1/jobs", json={"title": "", "description": "Build systems", "required_skills": [], "preferred_skills": [], "minimum_years_experience": 0})

    assert response.status_code == 422
