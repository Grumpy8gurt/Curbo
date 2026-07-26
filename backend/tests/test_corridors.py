def test_corridor_analysis_returns_expected_fields(client):
    road_id = client.get("/api/layers/roads").json()["features"][0]["properties"]["road_id"]
    response = client.post(
        "/api/corridors/analyze",
        json={"roadId": road_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["roadId"] == road_id
    assert "knownCurbRamps" in payload
    assert "bikeLanesNearby" in payload
    assert "userAnnotationsNearby" in payload
    assert "bikeLaneFeasibility" in payload
    assert isinstance(payload["planningNotes"], list)


def test_corridor_analysis_accepts_multiline_roads(client):
    road = client.app.state.store.roads["features"][0]
    road["geometry"] = {
        "type": "MultiLineString",
        "coordinates": [road["geometry"]["coordinates"]],
    }

    response = client.post(
        "/api/corridors/analyze",
        json={"roadId": road["properties"]["road_id"]},
    )

    assert response.status_code == 200
