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


def test_reviewer_notes_do_not_become_infrastructure_inventory(client):
    road = client.app.state.store.roads["features"][0]
    road_id = road["properties"]["road_id"]
    first_position = (
        road["geometry"]["coordinates"][0][0]
        if road["geometry"]["type"] == "MultiLineString"
        else road["geometry"]["coordinates"][0]
    )
    baseline = client.post("/api/corridors/analyze", json={"roadId": road_id}).json()

    for annotation_type in ("curb cut", "fire hydrant", "proposed bike lane"):
        geometry = (
            {
                "type": "LineString",
                "coordinates": [
                    first_position,
                    [first_position[0] + 0.00001, first_position[1] + 0.00001],
                ],
            }
            if annotation_type == "proposed bike lane"
            else {"type": "Point", "coordinates": first_position}
        )
        response = client.post(
            "/api/annotations",
            json={
                "annotationType": annotation_type,
                "description": f"Reviewer note for {annotation_type}",
                "geometry": geometry,
            },
        )
        assert response.status_code == 201

    updated = client.post("/api/corridors/analyze", json={"roadId": road_id}).json()

    assert updated["knownCurbRamps"] == baseline["knownCurbRamps"]
    assert updated["hydrantsNearby"] == baseline["hydrantsNearby"]
    assert updated["bikeLanesNearby"] == baseline["bikeLanesNearby"]
    assert updated["userAnnotationsNearby"] == baseline["userAnnotationsNearby"] + 3
