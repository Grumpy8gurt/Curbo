def test_roads_layer_returns_feature_collection(client):
    response = client.get("/api/layers/roads")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 13_000
    assert payload["features"][0]["properties"]["road_id"].startswith("road_")
    road_ids = [feature["properties"]["road_id"] for feature in payload["features"]]
    assert len(road_ids) == len(set(road_ids))
    named_features = [
        feature
        for feature in payload["features"]
        if feature["properties"]["name"] != "Unnamed road"
    ]
    assert len(named_features) / len(payload["features"]) > 0.99


def test_curb_ramps_layer_returns_feature_collection(client):
    response = client.get("/api/layers/sidewalk-ramps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert all(feature["geometry"]["type"] == "Point" for feature in payload["features"])

    alias_response = client.get("/api/layers/curb-ramps")
    assert alias_response.status_code == 200
    assert alias_response.json()["features"] == payload["features"]


def test_hydrants_layer_returns_feature_collection(client):
    response = client.get("/api/layers/hydrants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 1


def test_bike_lanes_layer_returns_feature_collection(client):
    response = client.get("/api/layers/bike-lanes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 1
    assert all(
        feature["geometry"]["type"] in {"LineString", "MultiLineString"}
        for feature in payload["features"]
    )


def test_layer_bbox_filter_preserves_metadata(client):
    unfiltered = client.get("/api/layers/roads").json()
    longitude, latitude = unfiltered["features"][0]["geometry"]["coordinates"][0]
    delta = 0.0001

    response = client.get(
        "/api/layers/roads",
        params={
            "bbox": (
                f"{longitude - delta},{latitude - delta},"
                f"{longitude + delta},{latitude + delta}"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 1 <= len(payload["features"]) <= len(unfiltered["features"])
    assert payload["metadata"]["status"] == "cached-eugene"


def test_layer_bbox_detects_line_segment_crossings(client):
    roads = client.get("/api/layers/roads").json()
    coordinates = roads["features"][0]["geometry"]["coordinates"]
    start, end = coordinates[0], coordinates[1]
    midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    epsilon = 1e-8

    response = client.get(
        "/api/layers/roads",
        params={
            "bbox": (
                f"{midpoint[0] - epsilon},{midpoint[1] - epsilon},"
                f"{midpoint[0] + epsilon},{midpoint[1] + epsilon}"
            )
        },
    )

    assert response.status_code == 200
    assert roads["features"][0] in response.json()["features"]


def test_layer_bbox_rejects_reversed_bounds(client):
    response = client.get("/api/layers/roads", params={"bbox": "1,1,0,0"})

    assert response.status_code == 422