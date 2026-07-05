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
