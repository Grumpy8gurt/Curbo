from __future__ import annotations

import math
from typing import Any

from fastapi import HTTPException

from app.schemas.corridors import CorridorAnalysisResponse


def parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    """
    Parse a bbox query parameter in the form "minLng,minLat,maxLng,maxLat".
    Returns None when no bbox was supplied, which signals the caller to skip
    spatial filtering and return the full layer.
    Raises HTTP 422 for any malformed or logically invalid input.
    """
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
    """Inclusive boundary test for a GeoJSON [lng, lat] point."""
    lng, lat = point
    min_lng, min_lat, max_lng, max_lat = bbox
    return min_lng <= lng <= max_lng and min_lat <= lat <= max_lat


def _segment_intersects_bbox(
    start: list[float],
    end: list[float],
    bbox: tuple[float, float, float, float],
) -> bool:
    """
    Liang–Barsky line-clipping test for a single segment against an axis-aligned bbox.

    Returns True when the segment intersects or lies within the bbox.
    The algorithm parameterises the segment as P(t) = start + t*(end-start),
    then clips t to [0, 1] by accumulating entering (t_min) and leaving (t_max)
    constraints from each of the four half-planes.  If t_min > t_max the segment
    misses the box entirely.

    Checking endpoint containment first short-circuits the arithmetic for the
    common case where both ends are inside the bbox.
    """
    if _point_within_bbox(start, bbox) or _point_within_bbox(end, bbox):
        return True

    min_lng, min_lat, max_lng, max_lat = bbox
    delta_lng = end[0] - start[0]
    delta_lat = end[1] - start[1]
    entering, leaving = 0.0, 1.0

    # Each tuple is (direction, distance) for the four clip planes.
    # direction < 0 means the ray is entering that half-plane → updates entering.
    # direction > 0 means the ray is leaving that half-plane → updates leaving.
    # direction == 0 means the segment is parallel; if distance < 0 it's outside.
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
    """Return True if any segment of a LineString intersects the bbox."""
    return any(
        _segment_intersects_bbox(coordinates[index], coordinates[index + 1], bbox)
        for index in range(len(coordinates) - 1)
    )


def filter_feature_collection(
    feature_collection: dict[str, Any], bbox: tuple[float, float, float, float] | None
) -> dict[str, Any]:
    """
    Return a new FeatureCollection containing only features that intersect the
    given bbox.  Passes through the collection unchanged when bbox is None.

    Supported geometry types: Point, LineString, MultiLineString.
    Features with other geometry types are silently excluded when a bbox is active.
    The original metadata dict is copied to the filtered result so callers can
    still read the layer status and source.
    """
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
    """
    Return the great-circle distance in metres between two [lng, lat] points
    using the Haversine formula.  Earth radius is approximated as 6,371,000 m.
    Sufficient accuracy for the sub-kilometre corridor buffers used in planning.
    """
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
    """Sum of Haversine distances for all consecutive vertex pairs in a LineString."""
    total = 0.0
    for index in range(len(coordinates) - 1):
        total += _haversine_meters(coordinates[index], coordinates[index + 1])
    return int(round(total))


def _expanded_bbox(coordinates: list[list[float]], buffer_meters: int) -> tuple[float, float, float, float]:
    """
    Compute an axis-aligned bounding box that contains all coordinates with an
    additional buffer in every direction.

    Latitude degrees are approximately constant in size (~111 320 m/degree).
    Longitude degrees shrink towards the poles by cos(latitude), so the buffer
    in the lng direction is divided by cos(mean_lat).  A floor of 0.1 on the
    cosine prevents division-by-zero near the poles (irrelevant for Eugene at
    ~44 °N but defensive).
    """
    lngs = [point[0] for point in coordinates]
    lats = [point[1] for point in coordinates]
    buffer_lat = buffer_meters / 111_320
    mean_lat = sum(lats) / len(lats)
    buffer_lng = buffer_meters / (111_320 * max(math.cos(math.radians(mean_lat)), 0.1))
    return min(lngs) - buffer_lng, min(lats) - buffer_lat, max(lngs) + buffer_lng, max(lats) + buffer_lat


def _flatten_line_coordinates(geometry: dict[str, Any]) -> list[list[float]]:
    """
    Return a flat list of [lng, lat] positions from a LineString or
    MultiLineString geometry so that the bbox and length calculations can work
    with a single coordinate sequence.
    """
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") == "MultiLineString":
        return [point for line in coordinates for point in line]
    return coordinates


def _count_near_features(
    feature_collection: dict[str, Any], bbox: tuple[float, float, float, float]
) -> int:
    """Count the number of features from a collection that fall within the bbox."""
    return len(filter_feature_collection(feature_collection, bbox).get("features", []))


def analyze_corridor(store, road_id: str, buffer_meters: int) -> CorridorAnalysisResponse:
    """
    Compute a planning summary for the corridor around a given road segment.

    Algorithm:
      1. Look up the road feature by ID in the store.
      2. Flatten its coordinates and build an expanded bbox with the requested
         buffer distance.
      3. Count features from each layer that fall within the bbox.
      4. Compute a simple feasibility score:
           base 4  +  up to 2 for existing bike lanes
                   -  missing curb-cut annotations
                   -  up to 2 for hydrant density (potential curbside constraint)
      5. Map the score to a Low/Medium/High label for the report.

    Limitations at prototype scale:
    - Does not use actual road geometry for proximity; the bbox is a rectangle
      aligned to the road extent, not a true buffer polygon.
    - Bus stops and parking conflicts are always 0 (no data source yet).
    """
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

    # Feasibility heuristic: starts at 4, improved by bike-lane presence,
    # reduced by missing curb cuts and hydrant density.
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
