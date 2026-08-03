from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable


FeatureCollection = dict[str, Any]


class EugeneDataService:
    """
    Load and normalize cached City of Eugene GIS layers into a consistent
    internal schema.

    The City's ArcGIS REST exports use inconsistent field names across
    snapshots (e.g. SEG_ID vs EUGID vs road_id for roads).  Each _normalize_*
    method resolves these aliases into a canonical set of properties so the
    rest of the application can rely on a stable contract regardless of which
    snapshot was cached.

    Loading strategy (per layer):
      1. Primary path  — data/eugene/<filename>.geojson
      2. Fallback path — data/sample/<fallback_filename>.geojson
      3. Empty collection with status="unavailable" if both are missing
    """

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
        """
        Load all four layers.  The returned dict key names match AppStore field
        names exactly, so `AppStore.from_collections(**load_all())` works.
        Note: sidewalk_ramps is stored under "curb_ramps" to match the frontend
        layer ID and the /api/layers/curb-ramps alias endpoint.
        """
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
            # bike_lanes has no sample fallback — returns empty if cache absent.
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
        """
        Read, validate, and normalise a single GeoJSON layer.

        Features with null geometry or non-dict properties are silently dropped
        to prevent downstream failures on malformed city exports.  deepcopy is
        used so that the normaliser can mutate features safely without
        corrupting the raw parsed data.
        """
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
        """
        Resolve road ID and name from multiple possible ArcGIS field aliases:
          road_id  — already-normalised cache
          SEG_ID   — Eugene street segment identifier
          EUGID    — older Eugene GIS export
          feature id / index  — last-resort synthetic ID

        road_id is prefixed with "road_" to namespace it across layers.
        classification is lowercased for consistent filtering.
        """
        raw = feature["properties"]
        road_id = str(
            raw.get("road_id")
            or raw.get("OBJECTID")
            or raw.get("SEG_ID")
            or raw.get("EUGID")
            or feature.get("id")
            or index
        )
        normalized_road_id = road_id if road_id.startswith("road_") else f"road_{road_id}"
        road_name = next(
            (
                str(raw.get(field)).strip()
                for field in ("name", "AIRSNAME", "NAME")
                if raw.get(field) and str(raw.get(field)).strip()
            ),
            "Unnamed road",
        )
        properties = {
            "road_id": normalized_road_id,
            "name": road_name,
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
        """
        Normalise curb/sidewalk ramp features from the Eugene pedestrian
        facilities export.

        Ramp_Truncated_Dome == 1 indicates a detectable-warning surface is
        present, which is used as a proxy for ADA compliance when the
        condition field is absent.
        """
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
            # Eugene publishes widths in feet and slopes/grades as percentages.
            # Keep left/right measurements because dual ramps often have no
            # single aggregate Curb_Ramp_* value.
            "width_feet": raw.get("width_feet", raw.get("Curb_Ramp_Width")),
            "left_width_feet": raw.get(
                "left_width_feet", raw.get("Curb_RampL_Width")
            ),
            "right_width_feet": raw.get(
                "right_width_feet", raw.get("Curb_RampR_Width")
            ),
            "grade_percent": raw.get(
                "grade_percent", raw.get("Curb_Ramp_Grade")
            ),
            "cross_slope_percent": raw.get(
                "cross_slope_percent", raw.get("Curb_Ramp_Cross_Slope")
            ),
            "left_cross_slope_percent": raw.get(
                "left_cross_slope_percent", raw.get("Curb_RampL_Cross_Slope")
            ),
            "right_cross_slope_percent": raw.get(
                "right_cross_slope_percent", raw.get("Curb_RampR_Cross_Slope")
            ),
            "source": "City of Eugene GIS",
        }
        feature["id"] = properties["ramp_id"]
        feature["properties"] = properties
        return feature

    @staticmethod
    def _normalize_hydrant(feature: dict[str, Any], index: int) -> dict[str, Any]:
        """
        Normalise fire hydrant features.  elog_id is the Eugene water utility's
        enterprise-log identifier, preferred over the generic OBJECTID when
        present.
        """
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
        """
        Normalise bike lane / bicycle facility features.

        facility_type resolves three possible ArcGIS field aliases:
          facility_type — already-normalised
          ftypedes      — free-text description from older exports
          ftype         — numeric code (kept as-is when no description exists)
        """
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
