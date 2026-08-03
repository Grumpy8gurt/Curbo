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
        json={"status": "reviewed"},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["properties"]["status"] == "reviewed"
    assert Path(client.app.state.settings.resolved_annotation_file).exists()


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
        json={"status": "reviewed"},
    )

    assert response.status_code == 404
