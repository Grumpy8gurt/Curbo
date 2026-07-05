from __future__ import annotations

from typing import Any


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _make_bbox(width: int, height: int) -> list[int]:
    box_width = max(24, int(width * 0.22))
    box_height = max(24, int(height * 0.18))
    center_x = width // 2
    center_y = int(height * 0.72)

    left = _clamp(center_x - box_width // 2, 0, max(width - 1, 0))
    top = _clamp(center_y - box_height // 2, 0, max(height - 1, 0))
    right = _clamp(left + box_width, left + 1, width)
    bottom = _clamp(top + box_height, top + 1, height)
    return [left, top, right, bottom]


def _make_confidence(width: int, height: int) -> float:
    confidence = 0.68 + ((width + height) % 11) * 0.01
    return round(min(confidence, 0.79), 2)


def _estimated_location(latitude: float | None, longitude: float | None) -> dict[str, Any] | None:
    if latitude is None or longitude is None:
        return None
    return {
        "type": "Point",
        "coordinates": [round(longitude, 6), round(latitude, 6)],
    }


def run_mock_detection(
    *,
    width: int,
    height: int,
    latitude: float | None,
    longitude: float | None,
) -> list[dict[str, Any]]:
    return [
        {
            "label": "possible_curb_cut",
            "confidence": _make_confidence(width, height),
            "bbox": _make_bbox(width, height),
            "estimated_location": _estimated_location(latitude, longitude),
            "review_status": "pending",
        }
    ]
