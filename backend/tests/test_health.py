def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "curbo-backend"}


def test_health_reports_configured_database_failure(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(
        database_url="missing-driver://database",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
    )

    with TestClient(create_app(settings)) as unavailable_client:
        response = unavailable_client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "not-ready"


def test_protected_routes_require_api_key(tmp_path):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    settings = Settings(
        auth_required=True,
        api_key="a-secure-test-key-that-is-long-enough",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
    )

    with TestClient(create_app(settings)) as protected_client:
        denied = protected_client.get("/api/annotations")
        allowed = protected_client.get(
            "/api/annotations",
            headers={"X-API-Key": "a-secure-test-key-that-is-long-enough"},
        )

    assert denied.status_code == 401
    assert allowed.status_code == 200
