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
    return {
        "roads": roads,
        "curb_ramps": curb_ramps,
        "hydrants": hydrants,
        "bike_lanes": {"type": "FeatureCollection", "features": []},
    }


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


@dataclass
class AppStore:
    roads: dict[str, Any]
    curb_ramps: dict[str, Any]
    hydrants: dict[str, Any]
    bike_lanes: dict[str, Any]
    annotations: list[dict[str, Any]] = field(default_factory=_default_annotations)
    annotation_file: Path | None = None
    reports: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, int] = field(
        default_factory=lambda: {"annotation": 2, "report": 0}
    )

    @classmethod
    def from_sample_dir(
        cls, sample_data_dir: Path, annotation_file: Path | None = None
    ) -> "AppStore":
        collections = build_sample_collections(sample_data_dir)
        return cls.from_collections(collections, annotation_file)

    @classmethod
    def from_collections(
        cls,
        collections: dict[str, dict[str, Any]],
        annotation_file: Path | None = None,
    ) -> "AppStore":
        annotations = cls._load_annotations(annotation_file)
        store = cls(
            **collections,
            annotations=annotations,
            annotation_file=annotation_file,
        )
        store.counters["annotation"] = max(
            [
                int(item["id"].split("_")[-1])
                for item in annotations
                if item.get("id", "").split("_")[-1].isdigit()
            ],
            default=0,
        )
        return store

    @staticmethod
    def _load_annotations(annotation_file: Path | None) -> list[dict[str, Any]]:
        if annotation_file is None or not annotation_file.exists():
            return _default_annotations()
        try:
            with annotation_file.open("r", encoding="utf-8") as handle:
                items = json.load(handle)
            for item in items:
                item["created_at"] = datetime.fromisoformat(item["created_at"])
            return items
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return _default_annotations()

    def _persist_annotations(self) -> None:
        if self.annotation_file is None:
            return
        self.annotation_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = [
            {**annotation, "created_at": annotation["created_at"].isoformat()}
            for annotation in self.annotations
        ]
        temporary_path = self.annotation_file.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as handle:
            json.dump(serialized, handle, indent=2)
        temporary_path.replace(self.annotation_file)

    def next_id(self, kind: str) -> str:
        self.counters[kind] += 1
        prefixes = {
            "annotation": "ann",
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
        self._persist_annotations()
        return annotation

    def update_annotation(self, annotation_id: str, status: str) -> dict[str, Any] | None:
        for annotation in self.annotations:
            if annotation["id"] == annotation_id:
                annotation["status"] = status
                self._persist_annotations()
                return annotation
        return None

    def get_annotations_feature_collection(self) -> dict[str, Any]:
        features = [self.annotation_to_feature(annotation) for annotation in self.list_annotations()]
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
