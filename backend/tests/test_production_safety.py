import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_production_settings_reject_missing_security_controls():
    with pytest.raises(ValidationError, match="AUTH_REQUIRED"):
        Settings(environment="production")


def test_production_settings_reject_sample_data_mode():
    with pytest.raises(ValidationError, match="ALLOW_SAMPLE_DATA"):
        Settings(
            environment="production",
            auth_required=True,
            api_key="a-production-key-that-is-at-least-32-characters",
            database_required=True,
            database_url="postgresql+psycopg2://curbo:secret@database/curbo",
            cors_origins=["https://curbo.example.com"],
            trusted_hosts=["curbo.example.com"],
            postgres_password="not-the-default-password",
        )


def test_mutation_rate_limit_and_security_headers(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
        mutation_rate_limit_per_minute=1,
    )

    with TestClient(create_app(settings)) as client:
        first = client.post(
            "/api/annotations",
            json={
                "annotationType": "other",
                "description": "First allowed write",
                "latitude": 44.052,
                "longitude": -123.075,
            },
        )
        limited = client.post(
            "/api/annotations",
            json={
                "annotationType": "other",
                "description": "Second write is limited",
                "latitude": 44.052,
                "longitude": -123.075,
            },
        )

    assert first.status_code == 201
    assert first.headers["X-Content-Type-Options"] == "nosniff"
    assert first.headers["X-Frame-Options"] == "DENY"
    assert limited.status_code == 429
    assert limited.headers["Retry-After"] == "60"


def test_request_body_limit_is_enforced_before_schema_validation(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(tmp_path / "annotations.json"),
        max_request_body_bytes=16_384,
    )

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/annotations",
            content=b"x" * 16_385,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 413
