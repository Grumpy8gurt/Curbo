from __future__ import annotations

import json
import hashlib
import os
import tempfile
import threading
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.annotation import Annotation
from app.models.corridor_report import CorridorReport

try:
    import fcntl
except ImportError:  # pragma: no cover - CURBO production images are Linux based
    fcntl = None


_PATH_LOCKS: dict[str, threading.RLock] = {}
_PATH_LOCKS_GUARD = threading.Lock()


class ConcurrencyConflictError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


_ALLOWED_STATUS_TRANSITIONS = {
    "pending": {"reviewed", "confirmed", "rejected"},
    "reviewed": {"confirmed", "rejected"},
    "confirmed": set(),
    "rejected": set(),
}


def _shared_thread_lock(path: Path | None) -> threading.RLock:
    key = str(path.resolve()) if path else "memory"
    with _PATH_LOCKS_GUARD:
        return _PATH_LOCKS.setdefault(key, threading.RLock())


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
    """New stores are empty; sample records belong in explicit test fixtures."""
    return []


@dataclass
class AppStore:
    """
    In-memory store for all GIS layers and planner annotations.

    Design decisions:
    - All layer data is held as raw GeoJSON dicts rather than Pydantic models
      to avoid the cost of deserialising the ~13 k-feature Eugene roads layer
      on every API request.  Routers validate outbound responses via
      response_model so the contract is still enforced at the boundary.
    - Annotations and report metadata use database transactions when a session
      factory is configured. Local annotations otherwise use a locked atomic
      JSON write so partial or concurrent writes do not corrupt the store.
    - UUID-based IDs avoid process-local counters and remain safe across
      restarts and independently running application instances.
    """

    roads: dict[str, Any]
    curb_ramps: dict[str, Any]
    hydrants: dict[str, Any]
    bike_lanes: dict[str, Any]
    annotations: list[dict[str, Any]] = field(default_factory=list)
    annotation_file: Path | None = None
    reports: list[dict[str, Any]] = field(default_factory=list)
    session_factory: sessionmaker[Session] | None = None
    _mutation_lock: threading.RLock = field(init=False, repr=False)
    _roads_by_id: dict[str, dict[str, Any]] = field(init=False, repr=False)
    _roads_etag: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._mutation_lock = _shared_thread_lock(self.annotation_file)
        self._roads_by_id = {
            feature.get("properties", {}).get("road_id"): feature
            for feature in self.roads.get("features", [])
            if feature.get("properties", {}).get("road_id")
        }
        digest = hashlib.sha256(
            json.dumps(self.roads, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self._roads_etag = f'"{digest}"'

    @property
    def roads_etag(self) -> str:
        return self._roads_etag

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
        session_factory: sessionmaker[Session] | None = None,
    ) -> "AppStore":
        annotations = [] if session_factory is not None else cls._load_annotations(annotation_file)
        return cls(
            **collections,
            annotations=annotations,
            annotation_file=annotation_file,
            session_factory=session_factory,
        )

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
            return []
        try:
            with annotation_file.open("r", encoding="utf-8") as handle:
                items = json.load(handle)
            for item in items:
                item["created_at"] = datetime.fromisoformat(item["created_at"])
                item.setdefault("version", 1)
            return items
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Annotation store '{annotation_file}' is invalid; "
                "restore or remove it before restarting CURBO."
            ) from exc

    @contextmanager
    def _file_lock(self):
        """Serialize writers across threads and processes sharing this file."""
        with self._mutation_lock:
            if self.annotation_file is None:
                yield
                return
            self.annotation_file.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.annotation_file.with_name(f"{self.annotation_file.name}.lock")
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _persist_annotations(self, annotations: list[dict[str, Any]]) -> None:
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
            for annotation in annotations
        ]
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.annotation_file.parent,
                prefix=f".{self.annotation_file.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(serialized, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, self.annotation_file)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def next_id(self, kind: str) -> str:
        """Return a collision-resistant identifier safe across workers and restarts."""
        prefixes = {
            "annotation": "ann",
            "report": "rep",
        }
        return f"{prefixes[kind]}_{uuid4().hex}"

    def get_road_feature(self, road_id: str) -> dict[str, Any] | None:
        """Use the startup-built index rather than scanning every road."""
        return self._roads_by_id.get(road_id)

    def list_annotations(self) -> list[dict[str, Any]]:
        """Return annotations sorted ascending by creation time."""
        if self.session_factory is not None:
            with self.session_factory() as session:
                rows = session.scalars(
                    select(Annotation).order_by(Annotation.created_at)
                ).all()
                return [self._database_annotation_to_dict(row) for row in rows]
        with self._file_lock():
            if self.annotation_file is not None:
                self.annotations = self._load_annotations(self.annotation_file)
            return sorted(deepcopy(self.annotations), key=lambda item: item["created_at"])

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
                "version": annotation.get("version", 1),
            },
        }

    def create_annotation(
        self, payload: dict[str, Any], *, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        """
        Create an annotation, assign an ID and default status, append it to the
        in-memory list, and flush to disk.  The caller is responsible for
        providing geometry, annotation_type, description, and source.
        """
        if self.session_factory is not None:
            return self._create_database_annotation(
                payload, idempotency_key=idempotency_key
            )
        with self._file_lock():
            current = (
                self._load_annotations(self.annotation_file)
                if self.annotation_file is not None
                else deepcopy(self.annotations)
            )
            if idempotency_key:
                existing = next(
                    (
                        item
                        for item in current
                        if item.get("idempotency_key") == idempotency_key
                    ),
                    None,
                )
                if existing is not None:
                    return deepcopy(existing)
            annotation = {
                "id": self.next_id("annotation"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
                "idempotency_key": idempotency_key,
                "version": 1,
                **payload,
            }
            candidate = [*current, annotation]
            self._persist_annotations(candidate)
            self.annotations = candidate
            return deepcopy(annotation)

    def update_annotation(
        self, annotation_id: str, status: str, *, expected_version: int
    ) -> dict[str, Any] | None:
        """Update the status of an existing annotation and persist.  Returns None if not found."""
        if self.session_factory is not None:
            with self.session_factory() as session:
                annotation = session.get(Annotation, annotation_id)
                if annotation is None:
                    return None
                self._validate_status_transition(annotation.status, status)
                result = session.execute(
                    update(Annotation)
                    .where(
                        Annotation.id == annotation_id,
                        Annotation.version == expected_version,
                    )
                    .values(status=status, version=Annotation.version + 1)
                )
                if result.rowcount != 1:
                    session.rollback()
                    raise ConcurrencyConflictError
                session.commit()
                updated = session.get(Annotation, annotation_id)
                assert updated is not None
                return self._database_annotation_to_dict(updated)
        with self._file_lock():
            current = (
                self._load_annotations(self.annotation_file)
                if self.annotation_file is not None
                else deepcopy(self.annotations)
            )
            candidate = deepcopy(current)
            for annotation in candidate:
                if annotation["id"] == annotation_id:
                    current_version = annotation.get("version", 1)
                    if current_version != expected_version:
                        raise ConcurrencyConflictError
                    self._validate_status_transition(annotation["status"], status)
                    annotation["status"] = status
                    annotation["version"] = current_version + 1
                    self._persist_annotations(candidate)
                    self.annotations = candidate
                    return deepcopy(annotation)
            return None

    @staticmethod
    def _validate_status_transition(current: str, requested: str) -> None:
        if requested == current:
            return
        if requested not in _ALLOWED_STATUS_TRANSITIONS.get(current, set()):
            raise InvalidTransitionError(f"Cannot change status from {current} to {requested}")

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
        if self.session_factory is not None:
            with self.session_factory() as session:
                row = CorridorReport(
                    id=report["id"],
                    road_id=report["road_id"],
                    include_layers=report.get("include_layers", []),
                    summary={"message": report.get("summary", "")},
                    format=report.get("format", "html"),
                    download_path=report["download_path"],
                )
                session.add(row)
                session.commit()
            return report
        self.reports.append(report)
        return report

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        if self.session_factory is not None:
            with self.session_factory() as session:
                row = session.get(CorridorReport, report_id)
                if row is None:
                    return None
                return {
                    "id": row.id,
                    "road_id": row.road_id,
                    "include_layers": row.include_layers,
                    "summary": row.summary.get("message", ""),
                    "format": row.format,
                    "download_path": row.download_path,
                }
        for report in self.reports:
            if report["id"] == report_id:
                return report
        return None

    @staticmethod
    def _database_annotation_to_dict(annotation: Annotation) -> dict[str, Any]:
        return {
            "id": annotation.id,
            "annotation_type": annotation.type,
            "description": annotation.description,
            "status": annotation.status,
            "source": annotation.source,
            "geometry": annotation.geometry,
            "created_at": annotation.created_at,
            "idempotency_key": annotation.idempotency_key,
            "version": annotation.version,
        }

    def _create_database_annotation(
        self, payload: dict[str, Any], *, idempotency_key: str | None
    ) -> dict[str, Any]:
        assert self.session_factory is not None
        with self.session_factory() as session:
            if idempotency_key:
                existing = session.scalar(
                    select(Annotation).where(
                        Annotation.idempotency_key == idempotency_key
                    )
                )
                if existing is not None:
                    return self._database_annotation_to_dict(existing)

            annotation = Annotation(
                id=self.next_id("annotation"),
                type=payload["annotation_type"],
                description=payload["description"],
                status="pending",
                source=payload["source"],
                geometry=payload["geometry"],
                idempotency_key=idempotency_key,
            )
            session.add(annotation)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                if not idempotency_key:
                    raise
                existing = session.scalar(
                    select(Annotation).where(
                        Annotation.idempotency_key == idempotency_key
                    )
                )
                if existing is None:
                    raise
                return self._database_annotation_to_dict(existing)
            session.refresh(annotation)
            return self._database_annotation_to_dict(annotation)
