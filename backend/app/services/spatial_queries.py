from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException

from app.schemas.corridors import CorridorAnalysisResponse


def parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None
    parts = [part.strip() for part in bbox.split(",")]
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be minLng,minLat,maxLng,maxLat")
    try:
        min_lng, min_lat, max_lng, max_lat = [float(part) for part in parts]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="bbox must contain numeric values") from exc
    values = (min_lng, min_lat, max_lng, max_lat)
    if not all(math.isfinite(value) for value in values):
        raise HTTPException(status_code=422, detail="bbox values must be finite")
    if min_lng > max_lng or min_lat > max_lat:
        raise HTTPException(status_code=422, detail="bbox minimums must not exceed maximums")
    return min_lng, min_lat, max_lng, max_lat


def _point_within_bbox(point: list[float], bbox: tuple[float, float, float, float]) -> bool:
    lng, lat = point
    min_lng, min_lat, max_lng, max_lat = bbox
    return min_lng <= lng <= max_lng and min_lat <= lat <= max_lat


def _segment_intersects_bbox(
    start: list[float],
    end: list[float],
    bbox: tuple[float, float, float, float],
) -> bool:
    if _point_within_bbox(start, bbox) or _point_within_bbox(end, bbox):
        return True

    min_lng, min_lat, max_lng, max_lat = bbox
    delta_lng = end[0] - start[0]
    delta_lat = end[1] - start[1]
    entering, leaving = 0.0, 1.0

    for direction, distance in (
        (-delta_lng, start[0] - min_lng),
        (delta_lng, max_lng - start[0]),
        (-delta_lat, start[1] - min_lat),
        (delta_lat, max_lat - start[1]),
    ):
        if direction == 0:
            if distance < 0:
                return False
            continue
        ratio = distance / direction
        if direction < 0:
            entering = max(entering, ratio)
        else:
            leaving = min(leaving, ratio)
        if entering > leaving:
            return False
    return True


def _line_intersects_bbox(
    coordinates: list[list[float]],
    bbox: tuple[float, float, float, float],
) -> bool:
    return any(
        _segment_intersects_bbox(coordinates[index], coordinates[index + 1], bbox)
        for index in range(len(coordinates) - 1)
    )


def filter_feature_collection(
    feature_collection: dict[str, Any], bbox: tuple[float, float, float, float] | None
) -> dict[str, Any]:
    if bbox is None:
        return feature_collection

    filtered_features = []
    for feature in feature_collection.get("features", []):
        geometry = feature.get("geometry", {})
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])
        if geometry_type == "Point" and _point_within_bbox(coordinates, bbox):
            filtered_features.append(feature)
        elif geometry_type == "LineString" and _line_intersects_bbox(coordinates, bbox):
            filtered_features.append(feature)
        elif geometry_type == "MultiLineString" and any(
            _line_intersects_bbox(line, bbox) for line in coordinates
        ):
            filtered_features.append(feature)

    filtered = {"type": "FeatureCollection", "features": filtered_features}
    if "metadata" in feature_collection:
        filtered["metadata"] = feature_collection["metadata"]
    return filtered


def _haversine_meters(first: list[float], second: list[float]) -> float:
    lng1, lat1 = first
    lng2, lat2 = second
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _line_length_meters(coordinates: list[list[float]]) -> int:
    total = 0.0
    for index in range(len(coordinates) - 1):
        total += _haversine_meters(coordinates[index], coordinates[index + 1])
    return int(round(total))


def _expanded_bbox(coordinates: list[list[float]], buffer_meters: int) -> tuple[float, float, float, float]:
    lngs = [point[0] for point in coordinates]
    lats = [point[1] for point in coordinates]
    buffer_lat = buffer_meters / 111_320
    mean_lat = sum(lats) / len(lats)
    buffer_lng = buffer_meters / (111_320 * max(math.cos(math.radians(mean_lat)), 0.1))
    return min(lngs) - buffer_lng, min(lats) - buffer_lat, max(lngs) + buffer_lng, max(lats) + buffer_lat


def _flatten_line_coordinates(geometry: dict[str, Any]) -> list[list[float]]:
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") == "MultiLineString":
        return [point for line in coordinates for point in line]
    return coordinates


def _count_near_features(
    feature_collection: dict[str, Any], bbox: tuple[float, float, float, float]
) -> int:
    return len(filter_feature_collection(feature_collection, bbox).get("features", []))


def analyze_corridor(store, road_id: str, buffer_meters: int) -> CorridorAnalysisResponse:
    road_feature = store.get_road_feature(road_id)
    if road_feature is None:
        raise HTTPException(status_code=404, detail=f"Road '{road_id}' was not found")

    road_properties = road_feature["properties"]
    road_coordinates = _flatten_line_coordinates(road_feature["geometry"])
    corridor_bbox = _expanded_bbox(road_coordinates, buffer_meters)

    known_curb_ramps = _count_near_features(store.curb_ramps, corridor_bbox)
    hydrants = _count_near_features(store.hydrants, corridor_bbox)
    bike_lanes = _count_near_features(store.bike_lanes, corridor_bbox)

    annotation_features = filter_feature_collection(
        store.get_annotations_feature_collection(), corridor_bbox
    )

    missing_curb_cuts = sum(
        1
        for feature in annotation_features["features"]
        if feature["properties"].get("annotation_type") == "missing curb cut"
    )
    annotation_count = len(annotation_features["features"])
    parking_conflicts = 0
    bus_stops = 0

    feasibility_score = 4 + min(bike_lanes, 2) - missing_curb_cuts - min(hydrants, 2)
    if feasibility_score >= 3:
        bike_lane_feasibility = "High"
    elif feasibility_score >= 1:
        bike_lane_feasibility = "Medium"
    else:
        bike_lane_feasibility = "Low"

    notes = []
    if missing_curb_cuts:
        notes.append("Possible missing curb cuts near the selected corridor should be field-checked.")
    if hydrants:
        notes.append("Hydrant spacing may constrain curbside redesign options.")
    if parking_conflicts:
        notes.append("Parking conflicts should be reviewed before committing to curb changes.")
    if not notes:
        notes.append("No major issues found in the cached Eugene layer analysis.")

    return CorridorAnalysisResponse(
        corridorId=f"cor_{road_id}",
        roadId=road_id,
        name=road_properties.get("name", road_id),
        knownCurbRamps=known_curb_ramps,
        possibleMissingCurbCuts=missing_curb_cuts,
        hydrantsNearby=hydrants,
        bikeLanesNearby=bike_lanes,
        userAnnotationsNearby=annotation_count,
        busStopsNearby=bus_stops,
        parkingConflicts=parking_conflicts,
        bikeLaneFeasibility=bike_lane_feasibility,
        planningNotes=notes,
    )
