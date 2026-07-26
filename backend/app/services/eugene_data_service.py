from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


FeatureCollection = dict[str, Any]


class EugeneDataService:
    """Load and normalize cached City of Eugene GIS layers."""

    FILES = {
        "roads": "roads.geojson",
        "sidewalk_ramps": "sidewalk_ramps.geojson",
        "hydrants": "hydrants.geojson",
        "bike_lanes": "bike_lanes.geojson",
    }

    def __init__(self, data_dir: Path, fallback_dir: Path):
        self.data_dir = data_dir
        self.fallback_dir = fallback_dir

    def load_all(self) -> dict[str, FeatureCollection]:
        return {
            "roads": self._load_layer(
                "roads", "roads.sample.geojson", self._normalize_road
            ),
            "curb_ramps": self._load_layer(
                "sidewalk_ramps",
                "curb_ramps.sample.geojson",
                self._normalize_sidewalk_ramp,
            ),
            "hydrants": self._load_layer(
                "hydrants", "hydrants.sample.geojson", self._normalize_hydrant
            ),
            "bike_lanes": self._load_layer(
                "bike_lanes", None, self._normalize_bike_lane
            ),
        }

    def _load_layer(
        self,
        layer_name: str,
        fallback_filename: str | None,
        normalizer: Callable[[dict[str, Any], int], dict[str, Any]],
    ) -> FeatureCollection:
        primary_path = self.data_dir / self.FILES[layer_name]
        path = primary_path
        data_status = "cached-eugene"

        if not path.exists() and fallback_filename:
            path = self.fallback_dir / fallback_filename
            data_status = "sample-fallback"

        if not path.exists():
            return {
                "type": "FeatureCollection",
                "features": [],
                "metadata": {
                    "layer": layer_name,
                    "status": "unavailable",
                    "source": "local-cache",
                },
            }

        with path.open("r", encoding="utf-8") as handle:
            collection = json.load(handle)

        if collection.get("type") != "FeatureCollection":
            raise ValueError(f"{path} is not a GeoJSON FeatureCollection")

        features = [
            normalizer(deepcopy(feature), index)
            for index, feature in enumerate(collection.get("features", []), start=1)
            if feature.get("geometry") and isinstance(feature.get("properties"), dict)
        ]
        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "layer": layer_name,
                "status": data_status,
                "source": "City of Eugene GIS cache",
            },
        }

    @staticmethod
    def _normalize_road(feature: dict[str, Any], index: int) -> dict[str, Any]:
        raw = feature["properties"]
        road_id = str(
            raw.get("road_id")
            or raw.get("SEG_ID")
            or raw.get("EUGID")
            or feature.get("id")
            or index
        )
        normalized_road_id = road_id if road_id.startswith("road_") else f"road_{road_id}"
        properties = {
            "road_id": normalized_road_id,
            "name": raw.get("name") or raw.get("NAME") or raw.get("AIRSNAME") or "Unnamed road",
            "classification": str(
                raw.get("classification") or raw.get("FCLASS") or "unknown"
            ).lower(),
            "source": "City of Eugene GIS",
        }
        feature["id"] = properties["road_id"]
        feature["properties"] = properties
        return feature

    @staticmethod
    def _normalize_sidewalk_ramp(
        feature: dict[str, Any], index: int
    ) -> dict[str, Any]:
        raw = feature["properties"]
        ramp_id = str(
            raw.get("ramp_id")
            or raw.get("OBJECTID")
            or feature.get("id")
            or index
        )
        has_dome = raw.get("Ramp_Truncated_Dome")
        properties = {
            "ramp_id": f"ramp_{ramp_id}",
            "status": raw.get("status") or "existing",
            "condition": raw.get("condition")
            or ("detectable warning present" if has_dome == 1 else "not assessed"),
            "configuration": raw.get("Ramp_Configuration") or "unknown",
            "source": "City of Eugene GIS",
        }
        feature["id"] = properties["ramp_id"]
        feature["properties"] = properties
        return feature

    @staticmethod
    def _normalize_hydrant(feature: dict[str, Any], index: int) -> dict[str, Any]:
        raw = feature["properties"]
        hydrant_id = str(
            raw.get("hydrant_id")
            or raw.get("OBJECTID")
            or raw.get("elog_id")
            or feature.get("id")
            or index
        )
        properties = {
            "hydrant_id": f"hydrant_{hydrant_id}",
            "flow_class": raw.get("flow_class") or "not published",
            "owner": raw.get("owner") or "unknown",
            "source": "City of Eugene GIS",
        }
        feature["id"] = properties["hydrant_id"]
        feature["properties"] = properties
        return feature

    @staticmethod
    def _normalize_bike_lane(
        feature: dict[str, Any], index: int
    ) -> dict[str, Any]:
        raw = feature["properties"]
        bike_lane_id = str(
            raw.get("bike_lane_id")
            or raw.get("bike_segid")
            or raw.get("OBJECTID")
            or feature.get("id")
            or index
        )
        properties = {
            "bike_lane_id": f"bike_{bike_lane_id}",
            "name": raw.get("name") or "Unnamed bicycle facility",
            "facility_type": raw.get("facility_type")
            or raw.get("ftypedes")
            or raw.get("ftype")
            or "unknown",
            "status": raw.get("status") or "unknown",
            "source": "City of Eugene GIS",
        }
        feature["id"] = properties["bike_lane_id"]
        feature["properties"] = properties
        return feature
