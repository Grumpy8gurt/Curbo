from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class DetectionService:
    """Mock curb-cut detection service with a future ML handoff seam."""

    def __init__(self, ml_base_url: str = "http://localhost:9000/detect") -> None:
        self.ml_base_url = ml_base_url

    def run_curb_cut_detection(self, image_record: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            return self._call_ml_service(image_record)
        except Exception:
            return self._fallback_detections(image_record)

    def _call_ml_service(self, image_record: dict[str, Any]) -> list[dict[str, Any]]:
        file_path = Path(image_record["file_path"])
        with file_path.open("rb") as handle:
            response = httpx.post(
                self.ml_base_url,
                files={"file": (image_record["filename"], handle, "application/octet-stream")},
                data={
                    "image_id": image_record["id"],
                    "latitude": image_record.get("latitude"),
                    "longitude": image_record.get("longitude"),
                    "road_id": image_record.get("road_id"),
                    "source": "backend",
                },
                timeout=5.0,
            )
        response.raise_for_status()
        payload = response.json()
        detections = payload.get("detections")
        if not isinstance(detections, list):
            raise ValueError("ML response did not contain a detections list")

        normalized = []
        for detection in detections:
            normalized.append(
                {
                    "label": self._normalize_label(detection.get("label")),
                    "confidence": float(detection.get("confidence", 0.72)),
                    "bbox": detection.get("bbox", [96, 72, 232, 188]),
                    "estimated_location": detection.get("estimated_location"),
                    "review_status": detection.get("review_status", "pending"),
                    "source": payload.get("model_version", "ml-service"),
                }
            )
        return normalized

    def _fallback_detections(self, image_record: dict[str, Any]) -> list[dict[str, Any]]:
        longitude = image_record.get("longitude")
        latitude = image_record.get("latitude")
        return [
            {
                "label": "Uploaded image curb-cut candidate",
                "confidence": 0.72,
                "bbox": [96, 72, 232, 188],
                "estimated_location": (
                    {
                        "type": "Point",
                        "coordinates": [round(longitude, 6), round(latitude, 6)],
                    }
                    if longitude is not None and latitude is not None
                    else None
                ),
                "review_status": "pending",
                "source": "backend-fallback",
            }
        ]

    def _normalize_label(self, label: Any) -> str:
        raw = str(label or "possible_curb_cut")
        return raw.replace("_", " ").title()
