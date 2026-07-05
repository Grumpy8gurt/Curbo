from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_road_features(feature_collection: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(feature_collection)
    for feature in normalized.get("features", []):
        properties = feature.setdefault("properties", {})
        road_id = properties.get("road_id")
        if road_id is None:
            road_id = properties.get("id") or "rd_unknown"
            properties["road_id"] = road_id
        feature["id"] = road_id
        properties.setdefault("source", "sample")
    return normalized


def _normalize_point_features(
    feature_collection: dict[str, Any], *, id_prefix: str, source: str = "sample"
) -> dict[str, Any]:
    normalized = deepcopy(feature_collection)
    for index, feature in enumerate(normalized.get("features", []), start=1):
        properties = feature.setdefault("properties", {})
        feature_id = f"{id_prefix}_{index}"
        properties["id"] = feature_id
        properties.setdefault("source", source)
    return normalized


def build_sample_collections(sample_data_dir: Path) -> dict[str, dict[str, Any]]:
    roads = _normalize_road_features(_load_geojson(sample_data_dir / "roads.sample.geojson"))
    curb_ramps = _normalize_point_features(
        _load_geojson(sample_data_dir / "curb_ramps.sample.geojson"),
        id_prefix="curb_ramp",
    )
    hydrants = _normalize_point_features(
        _load_geojson(sample_data_dir / "hydrants.sample.geojson"),
        id_prefix="hydrant",
    )
    return {"roads": roads, "curb_ramps": curb_ramps, "hydrants": hydrants}


def _default_annotations() -> list[dict[str, Any]]:
    return [
        {
            "id": "ann_001",
            "annotation_type": "missing curb cut",
            "description": "Northwest corner slope feels absent during field review.",
            "status": "pending",
            "source": "planner",
            "geometry": {"type": "Point", "coordinates": [-123.0894, 44.0519]},
            "created_at": datetime(2026, 7, 5, 15, 0, tzinfo=timezone.utc),
        },
        {
            "id": "ann_002",
            "annotation_type": "obstruction",
            "description": "Temporary sign blocks ramp access near the curb return.",
            "status": "pending",
            "source": "planner",
            "geometry": {"type": "Point", "coordinates": [-123.0874, 44.0493]},
            "created_at": datetime(2026, 7, 5, 15, 10, tzinfo=timezone.utc),
        },
    ]


def _default_detections() -> list[dict[str, Any]]:
    return [
        {
            "id": "det_001",
            "upload_id": "upl_sample_001",
            "label": "Possible missing curb cut",
            "confidence": 0.87,
            "bbox": [96, 72, 232, 188],
            "estimated_location": {"type": "Point", "coordinates": [-123.0906, 44.0517]},
            "review_status": "pending",
            "source": "mock-model",
            "created_at": datetime(2026, 7, 5, 15, 20, tzinfo=timezone.utc),
        },
        {
            "id": "det_002",
            "upload_id": "upl_sample_002",
            "label": "Possible curb ramp retrofit",
            "confidence": 0.71,
            "bbox": [88, 68, 220, 180],
            "estimated_location": {"type": "Point", "coordinates": [-123.0872, 44.0496]},
            "review_status": "confirmed",
            "source": "mock-model",
            "created_at": datetime(2026, 7, 5, 15, 25, tzinfo=timezone.utc),
        }
    ]


@dataclass
class AppStore:
    roads: dict[str, Any]
    curb_ramps: dict[str, Any]
    hydrants: dict[str, Any]
    annotations: list[dict[str, Any]] = field(default_factory=_default_annotations)
    detections: list[dict[str, Any]] = field(default_factory=_default_detections)
    uploaded_images: list[dict[str, Any]] = field(default_factory=list)
    reports: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, int] = field(
        default_factory=lambda: {"annotation": 2, "image": 0, "detection": 2, "report": 0}
    )

    @classmethod
    def from_sample_dir(cls, sample_data_dir: Path) -> "AppStore":
        collections = build_sample_collections(sample_data_dir)
        return cls(**collections)

    def next_id(self, kind: str) -> str:
        self.counters[kind] += 1
        prefixes = {
            "annotation": "ann",
            "image": "upl",
            "detection": "det",
            "report": "rep",
        }
        return f"{prefixes[kind]}_{self.counters[kind]:03d}"

    def get_road_feature(self, road_id: str) -> dict[str, Any] | None:
        for feature in self.roads.get("features", []):
            if feature.get("properties", {}).get("road_id") == road_id:
                return feature
        return None

    def list_annotations(self) -> list[dict[str, Any]]:
        return sorted(self.annotations, key=lambda item: item["created_at"])

    def annotation_to_feature(self, annotation: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "Feature",
            "id": annotation["id"],
            "geometry": annotation["geometry"],
            "properties": {
                "annotation_id": annotation["id"],
                "annotation_type": annotation["annotation_type"],
                "description": annotation["description"],
                "status": annotation["status"],
                "source": annotation["source"],
                "created_at": annotation["created_at"].isoformat(),
            },
        }

    def create_annotation(self, payload: dict[str, Any]) -> dict[str, Any]:
        annotation = {
            "id": self.next_id("annotation"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            **payload,
        }
        self.annotations.append(annotation)
        return annotation

    def update_annotation(self, annotation_id: str, status: str) -> dict[str, Any] | None:
        for annotation in self.annotations:
            if annotation["id"] == annotation_id:
                annotation["status"] = status
                return annotation
        return None

    def get_annotations_feature_collection(self) -> dict[str, Any]:
        features = [self.annotation_to_feature(annotation) for annotation in self.list_annotations()]
        return {"type": "FeatureCollection", "features": features}

    def create_upload(self, payload: dict[str, Any]) -> dict[str, Any]:
        image_record = {"id": self.next_id("image"), **payload}
        self.uploaded_images.append(image_record)
        return image_record

    def get_upload(self, image_id: str) -> dict[str, Any] | None:
        for uploaded_image in self.uploaded_images:
            if uploaded_image["id"] == image_id:
                return uploaded_image
        return None

    def add_detections(self, upload_id: str, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        stored_detections = []
        for detection in detections:
            stored = {
                "id": self.next_id("detection"),
                "upload_id": upload_id,
                "created_at": datetime.now(timezone.utc),
                "source": detection.get("source", "ml-service"),
                **detection,
            }
            self.detections.append(stored)
            stored_detections.append(stored)
        return stored_detections

    def update_detection(self, detection_id: str, review_status: str) -> dict[str, Any] | None:
        for detection in self.detections:
            if detection["id"] == detection_id:
                detection["review_status"] = review_status
                return detection
        return None

    def detection_to_feature(self, detection: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "Feature",
            "id": detection["id"],
            "geometry": detection["estimated_location"]
            or {"type": "Point", "coordinates": [-123.0868, 44.0521]},
            "properties": {
                "detection_id": detection["id"],
                "label": detection["label"],
                "confidence": detection["confidence"],
                "review_status": detection["review_status"],
                "upload_id": detection.get("upload_id"),
                "source": detection.get("source", "mock-detection"),
                "bbox": detection.get("bbox"),
            },
        }

    def get_detections_feature_collection(self) -> dict[str, Any]:
        features = [self.detection_to_feature(detection) for detection in self.detections]
        return {"type": "FeatureCollection", "features": features}

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = payload.copy()
        report.setdefault("id", self.next_id("report"))
        self.reports.append(report)
        return report

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        for report in self.reports:
            if report["id"] == report_id:
                return report
        return None
