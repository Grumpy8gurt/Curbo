from pathlib import Path


def test_annotation_can_be_created_and_updated(client):
    create_response = client.post(
        "/api/annotations",
        json={
            "annotationType": "missing curb cut",
            "description": "No visible curb ramp at the southeast corner.",
            "latitude": 44.052,
            "longitude": -123.075,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["type"] == "Feature"
    assert created["properties"]["status"] == "pending"
    assert created["properties"]["annotation_type"] == "missing curb cut"

    patch_response = client.patch(
        f"/api/annotations/{created['properties']['annotation_id']}",
        json={"status": "reviewed", "expectedVersion": 1},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["properties"]["status"] == "reviewed"
    database_path = Path(client.app.state.settings.resolved_database_url.removeprefix("sqlite:///"))
    assert database_path.exists()


def test_annotation_rejects_invalid_coordinates(client):
    response = client.post(
        "/api/annotations",
        json={
            "annotationType": "other",
            "description": "Invalid latitude",
            "latitude": 100,
            "longitude": -123.075,
        },
    )

    assert response.status_code == 422


def test_line_annotation_can_be_created(client):
    response = client.post(
        "/api/annotations",
        json={
            "annotationType": "proposed bike lane",
            "description": "Connect the existing facilities through this block.",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-123.091, 44.051],
                    [-123.089, 44.052],
                    [-123.087, 44.0525],
                ],
            },
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["geometry"]["type"] == "LineString"
    assert len(created["geometry"]["coordinates"]) == 3
    assert created["properties"]["annotation_type"] == "proposed bike lane"


def test_line_annotation_requires_two_positions(client):
    response = client.post(
        "/api/annotations",
        json={
            "annotationType": "bike lane gap",
            "description": "Incomplete sketch",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-123.091, 44.051]],
            },
        },
    )

    assert response.status_code == 422


def test_annotation_rejects_out_of_range_explicit_geometry(client):
    point_response = client.post(
        "/api/annotations",
        json={
            "annotationType": "curb cut",
            "description": "Invalid explicit point",
            "geometry": {"type": "Point", "coordinates": [999, 44.052]},
        },
    )
    line_response = client.post(
        "/api/annotations",
        json={
            "annotationType": "bike lane gap",
            "description": "Invalid explicit line",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-123.09, 44.052], [-123.08, 999]],
            },
        },
    )

    assert point_response.status_code == 422
    assert line_response.status_code == 422


def test_annotation_update_returns_not_found_for_unknown_id(client):
    response = client.patch(
        "/api/annotations/ann_missing",
        json={"status": "reviewed", "expectedVersion": 1},
    )

    assert response.status_code == 404


def test_annotation_rejects_spoofed_source(client):
    response = client.post(
        "/api/annotations",
        json={
            "annotationType": "other",
            "description": "Spoofed source",
            "latitude": 44.052,
            "longitude": -123.075,
            "source": "City of Eugene GIS",
        },
    )

    assert response.status_code == 422


def test_annotation_rejects_excessive_line_vertices(client):
    response = client.post(
        "/api/annotations",
        json={
            "annotationType": "other",
            "description": "Too many vertices",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-123.075, 44.052] for _ in range(1001)],
            },
        },
    )

    assert response.status_code == 422


def test_annotation_create_is_idempotent(client):
    payload = {
        "annotationType": "other",
        "description": "Retry-safe create",
        "latitude": 44.052,
        "longitude": -123.075,
    }
    headers = {"Idempotency-Key": "test-retry-key-123"}

    first = client.post("/api/annotations", json=payload, headers=headers)
    second = client.post("/api/annotations", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(client.get("/api/annotations").json()["features"]) == 1


def test_annotation_update_rejects_stale_version(client):
    created = client.post(
        "/api/annotations",
        json={
            "annotationType": "other",
            "description": "Concurrent update check",
            "latitude": 44.052,
            "longitude": -123.075,
        },
    ).json()
    annotation_id = created["id"]

    first = client.patch(
        f"/api/annotations/{annotation_id}",
        json={"status": "reviewed", "expectedVersion": 1},
    )
    stale = client.patch(
        f"/api/annotations/{annotation_id}",
        json={"status": "rejected", "expectedVersion": 1},
    )

    assert first.status_code == 200
    assert first.json()["properties"]["version"] == 2
    assert stale.status_code == 409
