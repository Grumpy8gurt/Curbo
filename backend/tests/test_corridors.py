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


def test_corridor_concerns_follow_annotation_review_status(client):
    road = client.app.state.store.roads["features"][0]
    road_id = road["properties"]["road_id"]
    first_position = (
        road["geometry"]["coordinates"][0][0]
        if road["geometry"]["type"] == "MultiLineString"
        else road["geometry"]["coordinates"][0]
    )
    baseline = client.post("/api/corridors/analyze", json={"roadId": road_id}).json()
    created_ids = {}

    for annotation_type in (
        "bike lane gap",
        "intersection safety",
        "parking/loading conflict",
    ):
        response = client.post(
            "/api/annotations",
            json={
                "annotationType": annotation_type,
                "description": f"Status-aware {annotation_type} review",
                "geometry": {"type": "Point", "coordinates": first_position},
            },
        )
        assert response.status_code == 201
        created_ids[annotation_type] = response.json()["properties"]["annotation_id"]

    pending = client.post("/api/corridors/analyze", json={"roadId": road_id}).json()

    assert pending["bikeLaneGaps"] == baseline["bikeLaneGaps"] + 1
    assert (
        pending["intersectionSafetyConcerns"]
        == baseline["intersectionSafetyConcerns"] + 1
    )
    assert pending["parkingConflicts"] == baseline["parkingConflicts"] + 1
    assert pending["annotationsNeedingReview"] == baseline["annotationsNeedingReview"] + 3
    assert pending["reviewPriority"] == "High"
    assert pending["dataLimitation"].startswith("Screening only:")

    status_updates = {
        "bike lane gap": "rejected",
        "intersection safety": "rejected",
        "parking/loading conflict": "confirmed",
    }
    for annotation_type, status in status_updates.items():
        response = client.patch(
            f"/api/annotations/{created_ids[annotation_type]}",
            json={"status": status},
        )
        assert response.status_code == 200

    resolved = client.post("/api/corridors/analyze", json={"roadId": road_id}).json()

    assert resolved["bikeLaneGaps"] == baseline["bikeLaneGaps"]
    assert resolved["intersectionSafetyConcerns"] == baseline["intersectionSafetyConcerns"]
    assert resolved["parkingConflicts"] == baseline["parkingConflicts"] + 1
    assert resolved["annotationsNeedingReview"] == baseline["annotationsNeedingReview"]
    assert resolved["userAnnotationsNearby"] == baseline["userAnnotationsNearby"] + 3
    assert any("parking/loading conflict" in signal for signal in resolved["reviewSignals"])
