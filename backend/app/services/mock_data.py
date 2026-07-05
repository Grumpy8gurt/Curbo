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
    for index, feature in enumerate(normalized.get("features", []), start=1):
        properties = feature.setdefault("properties", {})
        road_id = f"road_{index}"
        properties["id"] = road_id
        properties["road_id"] = road_id
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
            "id": "annotation_1",
            "type": "missing_curb_cut",
            "description": "Potential missing curb cut at the southeast corner.",
            "status": "pending",
            "source": "sample",
            "geometry": {"type": "Point", "coordinates": [-123.091, 44.0515]},
            "created_at": datetime.now(timezone.utc),
        },
        {
            "id": "annotation_2",
            "type": "parking_conflict",
            "description": "On-street parking likely overlaps proposed curb extension.",
            "status": "pending",
            "source": "sample",
            "geometry": {"type": "Point", "coordinates": [-123.0897, 44.0491]},
            "created_at": datetime.now(timezone.utc),
        },
    ]


def _default_detections() -> list[dict[str, Any]]:
    return [
        {
            "id": "detection_1",
            "image_id": "img_sample_1",
            "label": "possible_curb_cut",
            "confidence": 0.74,
            "bbox": [64, 72, 210, 180],
            "estimated_location": {"type": "Point", "coordinates": [-123.0889, 44.0525]},
            "review_status": "pending",
            "created_at": datetime.now(timezone.utc),
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
        default_factory=lambda: {"annotation": 2, "image": 0, "detection": 1, "report": 0}
    )

    @classmethod
    def from_sample_dir(cls, sample_data_dir: Path) -> "AppStore":
        collections = build_sample_collections(sample_data_dir)
        return cls(**collections)

    def next_id(self, kind: str) -> str:
        self.counters[kind] += 1
        prefixes = {
            "annotation": "annotation",
            "image": "img",
            "detection": "detection",
            "report": "report",
        }
        return f"{prefixes[kind]}_{self.counters[kind]}"

    def get_road_feature(self, road_id: str) -> dict[str, Any] | None:
        for feature in self.roads.get("features", []):
            if feature.get("properties", {}).get("road_id") == road_id:
                return feature
        return None

    def list_annotations(self) -> list[dict[str, Any]]:
        return sorted(self.annotations, key=lambda item: item["created_at"])

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
        features = [
            {
                "type": "Feature",
                "geometry": annotation["geometry"],
                "properties": {
                    "id": annotation["id"],
                    "type": annotation["type"],
                    "status": annotation["status"],
                    "source": annotation["source"],
                    "description": annotation["description"],
                },
            }
            for annotation in self.list_annotations()
        ]
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

    def add_detections(self, image_id: str, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        stored_detections = []
        for detection in detections:
            stored = {
                "id": self.next_id("detection"),
                "image_id": image_id,
                "created_at": datetime.now(timezone.utc),
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

    def get_detections_feature_collection(self) -> dict[str, Any]:
        features = [
            {
                "type": "Feature",
                "geometry": detection["estimated_location"],
                "properties": {
                    "id": detection["id"],
                    "label": detection["label"],
                    "confidence": detection["confidence"],
                    "review_status": detection["review_status"],
                    "image_id": detection["image_id"],
                    "source": "mock-detection",
                },
            }
            for detection in self.detections
        ]
        return {"type": "FeatureCollection", "features": features}

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = {"id": self.next_id("report"), **payload}
        self.reports.append(report)
        return report

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        for report in self.reports:
            if report["id"] == report_id:
                return report
        return None
