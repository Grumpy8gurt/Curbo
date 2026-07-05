def test_detection_endpoint_returns_mock_detection(client):
    upload_response = client.post(
        "/api/uploads/images",
        files={"file": ("survey_photo.jpg", b"fake-image-bytes", "image/jpeg")},
        data={"latitude": "44.0524", "longitude": "-123.0751", "road_id": "road_1"},
    )

    assert upload_response.status_code == 201
    image_id = upload_response.json()["image_id"]

    detection_response = client.post("/api/detection/curb-cuts", json={"image_id": image_id})

    assert detection_response.status_code == 200
    payload = detection_response.json()
    assert payload["image_id"] == image_id
    assert len(payload["detections"]) == 1
    assert payload["detections"][0]["label"] == "possible_curb_cut"
