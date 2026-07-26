#!/usr/bin/env python3
"""Validate CURBO's cached and fallback GeoJSON files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORIES = (ROOT / "data" / "eugene", ROOT / "data" / "sample")


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
        if feature.get("type") != "Feature":
            errors.append(f"feature {index} type must be Feature")
        if not feature.get("geometry"):
            errors.append(f"feature {index} is missing geometry")
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
