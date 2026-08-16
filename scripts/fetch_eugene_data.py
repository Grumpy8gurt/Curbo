#!/usr/bin/env python3
"""Refresh CURBO's local Eugene GeoJSON cache from configured public URLs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from validate_geojson import validate


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "eugene"
LAYERS = {
    "roads": (
        "EUGENE_ROADS_URL",
        "roads.geojson",
        "https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugStLines/FeatureServer/0",
        "OBJECTID,SEG_ID,EUGID,FCLASS,NAME,AIRSNAME",
    ),
    "sidewalk_ramps": (
        "EUGENE_SIDEWALK_RAMPS_URL",
        "sidewalk_ramps.geojson",
        "https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugSidewalkRamps/FeatureServer/0",
        "*",
    ),
    "hydrants": (
        "EUGENE_HYDRANTS_URL",
        "hydrants.geojson",
        "https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugHydrants/FeatureServer/0",
        "*",
    ),
    "bike_lanes": (
        "EUGENE_BIKE_LANES_URL",
        "bike_lanes.geojson",
        "https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugBikeways/FeatureServer/0",
        "*",
    ),
}
MINIMUM_FEATURES = {
    "roads": 10_000,
    "sidewalk_ramps": 1_000,
    "hydrants": 1_000,
    "bike_lanes": 100,
}
MAX_RESPONSE_BYTES = 50 * 1024 * 1024


def fetch_geojson(url: str, out_fields: str = "*") -> dict:
    if "f=geojson" in url.lower():
        return _fetch_page(url)

    base_url = url.rstrip("/")
    query_endpoint = base_url if base_url.endswith("/query") else f"{base_url}/query"
    features = []
    page_size = 2_000

    for offset in range(0, 200_000, page_size):
        parameters = urlencode(
            {
                "where": "1=1",
                "outFields": out_fields,
                "returnGeometry": "true",
                "outSR": 4326,
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "f": "geojson",
            }
        )
        page = _fetch_page(f"{query_endpoint}?{parameters}")
        page_features = page.get("features", [])
        features.extend(page_features)
        if len(page_features) < page_size:
            return {"type": "FeatureCollection", "features": features}

    raise ValueError("pagination exceeded the 200,000 feature safety limit")


def _fetch_page(query_url: str) -> dict:
    parsed = urlparse(query_url)
    allowed_hosts = {
        host.strip().lower()
        for host in os.getenv("EUGENE_ALLOWED_HOSTS", "services3.arcgis.com").split(",")
        if host.strip()
    }
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in allowed_hosts:
        raise ValueError("data source must use HTTPS and an explicitly allowed host")
    request = Request(query_url, headers={"User-Agent": "CURBO-Sprint-3/1.0"})
    with urlopen(request, timeout=30) as response:
        raw_payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw_payload) > MAX_RESPONSE_BYTES:
        raise ValueError("response exceeds the 50 MB safety limit")
    payload = json.loads(raw_payload)
    if payload.get("type") != "FeatureCollection":
        raise ValueError("response is not a GeoJSON FeatureCollection")
    return payload


def normalize(collection: dict, layer_name: str, source_url: str) -> dict:
    features = []
    for index, feature in enumerate(collection.get("features", []), start=1):
        if not feature.get("geometry") or not isinstance(feature.get("properties"), dict):
            continue
        feature["id"] = feature.get("id") or f"{layer_name}_{index}"
        feature["properties"]["layer"] = layer_name
        if not feature["properties"].get("source"):
            feature["properties"]["source"] = "city-of-eugene-gis"
        features.append(feature)
    return {
        "type": "FeatureCollection",
        "metadata": {
            "layer": layer_name,
            "source": source_url,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        },
        "features": features,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--layer",
        action="append",
        choices=sorted(LAYERS),
        help="Refresh only this layer; repeat to select multiple layers.",
    )
    arguments = parser.parse_args()
    selected_layers = set(arguments.layer or LAYERS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0

    cache_only = os.getenv("EUGENE_CACHE_ONLY", "").lower() in {"1", "true", "yes"}

    for layer_name, (
        environment_name,
        filename,
        default_url,
        out_fields,
    ) in LAYERS.items():
        if layer_name not in selected_layers:
            continue
        destination = OUTPUT_DIR / filename
        url = None if cache_only else os.getenv(environment_name, default_url)

        if not url:
            cache_status = (
                f"using existing cache ({destination.name})"
                if destination.exists()
                else "no cache available"
            )
            print(f"SKIP {layer_name}: cache-only mode; {cache_status}.")
            if not destination.exists():
                failures += 1
            continue

        try:
            collection = normalize(fetch_geojson(url, out_fields), layer_name, url)
            feature_count = len(collection["features"])
            if feature_count < MINIMUM_FEATURES[layer_name]:
                raise ValueError(
                    f"received only {feature_count} features; expected at least "
                    f"{MINIMUM_FEATURES[layer_name]}"
                )
            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=OUTPUT_DIR,
                    prefix=f".{filename}.",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    temporary = Path(handle.name)
                    json.dump(collection, handle, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                errors = validate(temporary)
                if errors:
                    raise ValueError("validation failed: " + "; ".join(errors[:5]))
                temporary.replace(destination)
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
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
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
