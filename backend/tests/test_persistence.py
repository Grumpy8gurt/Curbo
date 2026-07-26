from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_annotations_persist_across_app_restarts(tmp_path):
    annotation_file = tmp_path / "annotations.json"
    settings = Settings(
        database_url="sqlite://",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(annotation_file),
    )

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/annotations",
            json={
                "annotationType": "other",
                "description": "Persistence restart check",
                "latitude": 44.0521,
                "longitude": -123.0868,
            },
        )
        assert response.status_code == 201
        annotation_id = response.json()["properties"]["annotation_id"]

    with TestClient(create_app(settings)) as restarted_client:
        payload = restarted_client.get("/api/annotations").json()

    persisted = next(
        feature
        for feature in payload["features"]
        if feature["properties"]["annotation_id"] == annotation_id
    )
    assert persisted["properties"]["description"] == "Persistence restart check"
