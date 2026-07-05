from __future__ import annotations

from io import BytesIO

from PIL import Image


def _make_test_image_bytes(width: int = 640, height: int = 480) -> bytes:
    image = Image.new("RGB", (width, height), color=(180, 190, 200))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_detect_accepts_valid_image_and_returns_detection(client):
    response = client.post(
        "/detect",
        files={"file": ("street.png", _make_test_image_bytes(), "image/png")},
        data={"image_id": "img_1", "latitude": "44.0524", "longitude": "-123.0751"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_id"] == "img_1"
    assert payload["model_version"] == "mock-v0.1"
    assert isinstance(payload["detections"], list)
    assert len(payload["detections"]) == 1
    detection = payload["detections"][0]
    assert detection["label"] == "possible_curb_cut"
    assert detection["estimated_location"]["coordinates"] == [-123.0751, 44.0524]


def test_detect_bbox_stays_within_image_dimensions(client):
    width = 320
    height = 200
    response = client.post(
        "/detect",
        files={"file": ("street.png", _make_test_image_bytes(width, height), "image/png")},
    )

    assert response.status_code == 200
    bbox = response.json()["detections"][0]["bbox"]
    left, top, right, bottom = bbox
    assert 0 <= left < right <= width
    assert 0 <= top < bottom <= height


def test_detect_rejects_non_image_file(client):
    response = client.post(
        "/detect",
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be an image"
