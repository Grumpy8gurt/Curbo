#!/usr/bin/env python3
"""Validate CURBO's cached and fallback GeoJSON files."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORIES = (ROOT / "data" / "eugene", ROOT / "data" / "sample")


def _valid_position(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and all(isinstance(item, (int, float)) and math.isfinite(item) for item in value[:2])
        and -180 <= value[0] <= 180
        and -90 <= value[1] <= 90
    )


def _valid_line(value: object) -> bool:
    return isinstance(value, list) and len(value) >= 2 and all(
        _valid_position(position) for position in value
    )


def _valid_geometry(geometry: object) -> bool:
    if not isinstance(geometry, dict):
        return False
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Point":
        return _valid_position(coordinates)
    if geometry_type == "LineString":
        return _valid_line(coordinates)
    if geometry_type == "MultiLineString":
        return isinstance(coordinates, list) and bool(coordinates) and all(
            _valid_line(line) for line in coordinates
        )
    return False


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read valid JSON: {exc}"]

    if payload.get("type") != "FeatureCollection":
        errors.append("root type must be FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        return errors + ["features must be a list"]

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            errors.append(f"feature {index} must be an object")
            continue
        if feature.get("type") != "Feature":
            errors.append(f"feature {index} type must be Feature")
        if not _valid_geometry(feature.get("geometry")):
            errors.append(
                f"feature {index} geometry must be a valid Point, LineString, "
                "or MultiLineString in longitude/latitude coordinates"
            )
        if not isinstance(feature.get("properties"), dict):
            errors.append(f"feature {index} properties must be an object")
    return errors


def main() -> int:
    paths = sorted(
        path
        for directory in DATA_DIRECTORIES
        if directory.exists()
        for path in directory.glob("*.geojson")
    )
    failures = 0

    for path in paths:
        errors = validate(path)
        relative_path = path.relative_to(ROOT)
        if errors:
            failures += 1
            print(f"FAIL {relative_path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {relative_path}")

    print(f"\nValidated {len(paths)} file(s): {len(paths) - failures} passed, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
