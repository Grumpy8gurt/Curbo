from __future__ import annotations

from typing import Any


class DetectionService:
    """Mock curb-cut detection service with a future ML handoff seam."""

    def __init__(self, ml_base_url: str = "http://localhost:9000/detect") -> None:
        self.ml_base_url = ml_base_url

    def run_curb_cut_detection(self, image_record: dict[str, Any]) -> list[dict[str, Any]]:
        longitude = image_record.get("longitude") or -123.0918
        latitude = image_record.get("latitude") or 44.0517
        return [
            {
                "label": "possible_curb_cut",
                "confidence": 0.78,
                "bbox": [120, 80, 240, 190],
                "estimated_location": {
                    "type": "Point",
                    "coordinates": [round(longitude + 0.0006, 6), round(latitude + 0.0004, 6)],
                },
                "review_status": "pending",
            }
        ]
