#!/usr/bin/env python3
"""Refresh CURBO's local Eugene GeoJSON cache from configured public URLs."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "eugene"
LAYERS = {
    "roads": (
        "EUGENE_ROADS_URL",
        "roads.geojson",
        "https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/2",
    ),
    "sidewalk_ramps": (
        "EUGENE_SIDEWALK_RAMPS_URL",
        "sidewalk_ramps.geojson",
        "https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/29",
    ),
    "hydrants": (
        "EUGENE_HYDRANTS_URL",
        "hydrants.geojson",
        "https://gis.eugene-or.gov/arcgis/rest/services/PWE/MiscInfra/MapServer/3",
    ),
    "bike_lanes": (
        "EUGENE_BIKE_LANES_URL",
        "bike_lanes.geojson",
        "https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/19",
    ),
}


def fetch_geojson(url: str) -> dict:
    separator = "&" if "?" in url else "?"
    query_url = (
        url
        if "f=geojson" in url.lower()
        else (
            f"{url}{separator}where=1%3D1&outFields=*&outSR=4326"
            "&resultRecordCount=1000&f=geojson"
        )
    )
    request = Request(query_url, headers={"User-Agent": "CURBO-Sprint-3/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("type") != "FeatureCollection":
        raise ValueError("response is not a GeoJSON FeatureCollection")
    return payload


def normalize(collection: dict, layer_name: str) -> dict:
    features = []
    for index, feature in enumerate(collection.get("features", []), start=1):
        if not feature.get("geometry") or not isinstance(feature.get("properties"), dict):
            continue
        feature["id"] = feature.get("id") or f"{layer_name}_{index}"
        feature["properties"]["layer"] = layer_name
        feature["properties"].setdefault("source", "city-of-eugene-gis")
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0

    cache_only = os.getenv("EUGENE_CACHE_ONLY", "").lower() in {"1", "true", "yes"}

    for layer_name, (environment_name, filename, default_url) in LAYERS.items():
        destination = OUTPUT_DIR / filename
        url = None if cache_only else os.getenv(environment_name, default_url)

        if not url:
            cache_status = (
                f"using existing cache ({destination.name})"
                if destination.exists()
                else "no cache available"
            )
            print(f"SKIP {layer_name}: cache-only mode; {cache_status}.")
            continue

        try:
            collection = normalize(fetch_geojson(url), layer_name)
            temporary = destination.with_suffix(".tmp")
            temporary.write_text(json.dumps(collection, indent=2), encoding="utf-8")
            temporary.replace(destination)
            print(f"FETCHED {layer_name}: {len(collection['features'])} features.")
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            failures += 1
            fallback = " Existing cache was preserved." if destination.exists() else ""
            print(f"FAILED {layer_name}: {exc}.{fallback}", file=sys.stderr)

    if failures:
        print(
            f"Completed with {failures} fetch failure(s); cached data remains usable.",
            file=sys.stderr,
        )
    else:
        print("Eugene data refresh complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
