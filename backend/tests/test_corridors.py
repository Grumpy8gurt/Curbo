def test_corridor_analysis_returns_expected_fields(client):
    response = client.post(
        "/api/corridors/analyze",
        json={"road_id": "road_1", "buffer_meters": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["road_id"] == "road_1"
    assert "known_curb_ramps" in payload
    assert "bike_lane_feasibility" in payload
    assert isinstance(payload["notes"], list)
