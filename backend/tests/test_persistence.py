from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.app_store import AppStore


def test_annotations_persist_across_app_restarts(tmp_path):
    annotation_file = tmp_path / "annotations.json"
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(annotation_file),
    )

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/annotations",
            json={
                "annotationType": "bike lane gap",
                "description": "Line persistence restart check",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-123.0868, 44.0521],
                        [-123.0855, 44.0524],
                    ],
                },
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
    assert persisted["properties"]["description"] == "Line persistence restart check"
    assert persisted["geometry"]["type"] == "LineString"
    assert persisted["geometry"]["coordinates"][1] == [-123.0855, 44.0524]


def test_annotation_review_status_persists_across_app_restarts(tmp_path):
    annotation_file = tmp_path / "annotations.json"
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'curbo.db'}",
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(annotation_file),
    )

    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/annotations",
            json={
                "annotationType": "parking/loading conflict",
                "description": "Confirm this decision survives restart",
                "latitude": 44.0521,
                "longitude": -123.0868,
            },
        ).json()
        annotation_id = created["properties"]["annotation_id"]
        update_response = client.patch(
            f"/api/annotations/{annotation_id}",
            json={"status": "confirmed", "expectedVersion": 1},
        )
        assert update_response.status_code == 200

    with TestClient(create_app(settings)) as restarted_client:
        payload = restarted_client.get("/api/annotations").json()

    persisted = next(
        feature
        for feature in payload["features"]
        if feature["properties"]["annotation_id"] == annotation_id
    )
    assert persisted["properties"]["status"] == "confirmed"


def test_invalid_annotation_store_fails_without_overwriting_data(tmp_path):
    annotation_file = tmp_path / "annotations.json"
    annotation_file.write_text("{not valid json", encoding="utf-8")
    settings = Settings(
        database_url=None,
        report_dir=str(tmp_path / "reports"),
        annotation_file=str(annotation_file),
    )

    with pytest.raises(ValueError, match="Annotation store"):
        with TestClient(create_app(settings)):
            pass

    assert annotation_file.read_text(encoding="utf-8") == "{not valid json"


def test_independent_stores_do_not_lose_concurrent_writes(tmp_path):
    annotation_file = tmp_path / "annotations.json"
    sample_dir = Settings().sample_data_dir
    first_store = AppStore.from_sample_dir(sample_dir, annotation_file)
    second_store = AppStore.from_sample_dir(sample_dir, annotation_file)

    def create(store, description):
        return store.create_annotation(
            {
                "annotation_type": "other",
                "description": description,
                "geometry": {"type": "Point", "coordinates": [-123.08, 44.05]},
                "source": "test reviewer",
            }
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(create, first_store, "first writer")
        second_future = executor.submit(create, second_store, "second writer")
        created_ids = {first_future.result()["id"], second_future.result()["id"]}

    restarted = AppStore.from_sample_dir(sample_dir, annotation_file)
    persisted = restarted.list_annotations()

    assert len(created_ids) == 2
    assert {item["id"] for item in persisted} == created_ids
