def test_roads_layer_returns_feature_collection(client):
    response = client.get("/api/layers/roads")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 1
    assert payload["features"][0]["properties"]["road_id"].startswith("road_")


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