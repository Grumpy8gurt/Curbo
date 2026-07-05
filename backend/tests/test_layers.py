def test_roads_layer_returns_feature_collection(client):
    response = client.get("/api/layers/roads")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 1
    assert payload["features"][0]["properties"]["road_id"].startswith("rd_")


def test_curb_ramps_layer_returns_feature_collection(client):
    response = client.get("/api/layers/curb-ramps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert all(feature["geometry"]["type"] == "Point" for feature in payload["features"])


def test_hydrants_layer_returns_feature_collection(client):
    response = client.get("/api/layers/hydrants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) >= 1


def test_detection_layer_returns_feature_collection(client):
    response = client.get("/api/detection/curb-cuts")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["detection_id"].startswith("det_")
