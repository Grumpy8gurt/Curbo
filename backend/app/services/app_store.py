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
    """
    Ensure every road feature in a sample collection has a road_id property
    and a matching top-level feature id.  Used only for sample data; the full
    Eugene cache is normalised by EugeneDataService instead.
    """
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
    """
    Assign synthetic sequential IDs to point features in sample collections
    where the raw data does not include stable identifiers.
    """
    normalized = deepcopy(feature_collection)
    for index, feature in enumerate(normalized.get("features", []), start=1):
        properties = feature.setdefault("properties", {})
        feature_id = f"{id_prefix}_{index}"
        properties["id"] = feature_id
        properties.setdefault("source", source)
    return normalized


def build_sample_collections(sample_data_dir: Path) -> dict[str, dict[str, Any]]:
    """
    Build the four layer collections from the compact sample GeoJSON files.
    bike_lanes returns an empty collection because no sample file exists for it.
    """
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
    """
    Seed annotations used when no annotation file exists yet.
    These represent planner-entered examples from the Eugene downtown corridor
    and are shown in the UI on first launch so the map is not empty.
    """
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
    """
    In-memory store for all GIS layers and planner annotations.

    Design decisions:
    - All layer data is held as raw GeoJSON dicts rather than Pydantic models
      to avoid the cost of deserialising the ~13 k-feature Eugene roads layer
      on every API request.  Routers validate outbound responses via
      response_model so the contract is still enforced at the boundary.
    - Annotations are the only writable entity; they are also persisted to
      a JSON file using an atomic write-then-rename pattern so partial writes
      never corrupt the store.
    - Counters track the numeric suffix of the last-issued ID for each entity
      kind so that IDs remain sequential across restarts when the annotation
      file is present.
    """

    roads: dict[str, Any]
    curb_ramps: dict[str, Any]
    hydrants: dict[str, Any]
    bike_lanes: dict[str, Any]
    annotations: list[dict[str, Any]] = field(default_factory=_default_annotations)
    annotation_file: Path | None = None
    reports: list[dict[str, Any]] = field(default_factory=list)
    # Counters are seeded from existing IDs at load time (see from_collections).
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
        # Seed the annotation counter from the highest existing ID so that new
        # annotations receive IDs that are strictly greater than any persisted one.
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
        """
        Load annotations from the JSON persistence file if it exists.
        created_at strings are parsed back to aware datetime objects so that
        list_annotations() can sort them correctly.

        Raises ValueError with a human-readable message when the file exists but
        is corrupt — this is intentional: a silent reset would silently discard
        planner work.
        """
        if annotation_file is None or not annotation_file.exists():
            return _default_annotations()
        try:
            with annotation_file.open("r", encoding="utf-8") as handle:
                items = json.load(handle)
            for item in items:
                item["created_at"] = datetime.fromisoformat(item["created_at"])
            return items
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Annotation store '{annotation_file}' is invalid; "
                "restore or remove it before restarting CURBO."
            ) from exc

    def _persist_annotations(self) -> None:
        """
        Atomically write the annotation list to disk.

        The write-to-tmp-then-rename pattern ensures the file on disk is never
        in a partially-written state, even if the process is killed mid-write.
        datetime objects are serialised to ISO 8601 strings for JSON compatibility.
        """
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
        # os.replace semantics: atomic on POSIX, best-effort on Windows.
        temporary_path.replace(self.annotation_file)

    def next_id(self, kind: str) -> str:
        """Increment the counter for `kind` and return a zero-padded ID string."""
        self.counters[kind] += 1
        prefixes = {
            "annotation": "ann",
            "report": "rep",
        }
        return f"{prefixes[kind]}_{self.counters[kind]:03d}"

    def get_road_feature(self, road_id: str) -> dict[str, Any] | None:
        """Linear scan of the roads layer; acceptable for prototype scale (~13 k features)."""
        for feature in self.roads.get("features", []):
            if feature.get("properties", {}).get("road_id") == road_id:
                return feature
        return None

    def list_annotations(self) -> list[dict[str, Any]]:
        """Return annotations sorted ascending by creation time."""
        return sorted(self.annotations, key=lambda item: item["created_at"])

    def annotation_to_feature(self, annotation: dict[str, Any]) -> dict[str, Any]:
        """
        Convert the internal annotation dict to a GeoJSON Feature suitable for
        API responses.  created_at is re-serialised to an ISO 8601 string here
        because the response_model expects a datetime-compatible value.
        """
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
        """
        Create an annotation, assign an ID and default status, append it to the
        in-memory list, and flush to disk.  The caller is responsible for
        providing geometry, annotation_type, description, and source.
        """
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
        """Update the status of an existing annotation and persist.  Returns None if not found."""
        for annotation in self.annotations:
            if annotation["id"] == annotation_id:
                annotation["status"] = status
                self._persist_annotations()
                return annotation
        return None

    def get_annotations_feature_collection(self) -> dict[str, Any]:
        """Return all annotations as a GeoJSON FeatureCollection sorted by creation time."""
        features = [self.annotation_to_feature(annotation) for annotation in self.list_annotations()]
        return {"type": "FeatureCollection", "features": features}

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Register a generated report in memory.  Reports are not persisted to
        disk between restarts; the HTML file itself is the durable artifact.
        """
        report = payload.copy()
        report.setdefault("id", self.next_id("report"))
        self.reports.append(report)
        return report

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        for report in self.reports:
            if report["id"] == report_id:
                return report
        return None
