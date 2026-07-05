def test_annotation_can_be_created_and_updated(client):
    create_response = client.post(
        "/api/annotations",
        json={
            "type": "missing_curb_cut",
            "description": "No visible curb ramp at the southeast corner.",
            "geometry": {"type": "Point", "coordinates": [-123.075, 44.052]},
            "source": "field_survey",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "pending"
    assert created["type"] == "missing_curb_cut"

    patch_response = client.patch(
        f"/api/annotations/{created['id']}",
        json={"status": "confirmed"},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "confirmed"
