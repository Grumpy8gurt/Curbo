def test_detection_endpoint_returns_mock_detection(client):
    upload_response = client.post(
        "/api/uploads/images",
        files={"image": ("survey_photo.jpg", b"fake-image-bytes", "image/jpeg")},
        data={"latitude": "44.0524", "longitude": "-123.0751", "road_id": "road_1"},
    )

    assert upload_response.status_code == 201
    upload_id = upload_response.json()["uploadId"]

    detection_response = client.post("/api/detection/curb-cuts", json={"upload_id": upload_id})

    assert detection_response.status_code == 200
    payload = detection_response.json()
    assert payload["type"] == "Feature"
    assert payload["properties"]["upload_id"] == upload_id
    assert payload["properties"]["detection_id"].startswith("det_")
