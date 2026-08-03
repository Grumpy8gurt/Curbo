# API Contract

This document reflects the verified CURBO Sprint 4 integration contract.

## Backend Routes

### `GET /api/health`

```json
{
  "status": "ok",
  "service": "curbo-backend"
}
```

### `GET /api/layers/roads`

- Response: GeoJSON `FeatureCollection`
- Road ids use the normalized Eugene shape, for example `road_20000641`

### `GET /api/layers/sidewalk-ramps`

- Response: GeoJSON `FeatureCollection`
- Available normalized measurements use `width_feet`,
  `left_width_feet`, `right_width_feet`, `grade_percent`,
  `cross_slope_percent`, `left_cross_slope_percent`, and
  `right_cross_slope_percent`. Values may be null when the City source does
  not publish a measurement.

### `GET /api/layers/curb-ramps`

- Compatibility alias for `/api/layers/sidewalk-ramps`

### `GET /api/layers/hydrants`

- Response: GeoJSON `FeatureCollection`

### `GET /api/layers/bike-lanes`

- Response: GeoJSON `FeatureCollection` containing `LineString` or `MultiLineString` features

### `GET /api/layers/annotations`

- Response: GeoJSON `FeatureCollection`

All infrastructure layer routes accept an optional
`bbox=minLng,minLat,maxLng,maxLat` query. Bounds must be finite and ordered;
points or line segments intersecting the box are returned.

### `GET /api/annotations`

- Purpose: return annotations in the same GeoJSON feature format the frontend stores in local state
- Geometry: `Point` or `LineString`
- Reviewer annotations are non-authoritative notes. They do not add to the City curb-ramp, hydrant, or bike-lane inventory counts.
- Supported types: `curb cut`, `missing curb cut`, `fire hydrant`, `bike lane gap`, `proposed bike lane`, `obstruction`, `parking/loading conflict`, `intersection safety`, `drainage/utility conflict`, `bad data`, and `other`
- Response:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "ann_001",
      "properties": {
        "annotation_id": "ann_001",
        "annotation_type": "missing curb cut",
        "description": "Northwest corner slope feels absent during field review.",
        "status": "pending",
        "source": "planner",
        "created_at": "2026-07-05T15:00:00+00:00"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-123.0894, 44.0519]
      }
    }
  ]
}
```

### `POST /api/annotations`

- Request:

```json
{
  "annotationType": "proposed bike lane",
  "description": "Connect the existing facilities through this block.",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-123.091, 44.0515],
      [-123.089, 44.052]
    ]
  }
}
```

- Point annotations may alternatively send `latitude` and `longitude` instead of `geometry`.
- Response: one annotation `Feature`

### `PATCH /api/annotations/{annotation_id}`

- Purpose: persist a user-selected review state from the map popup
- Supported states: `pending`, `reviewed`, `confirmed`, and `rejected`
- Request:

```json
{
  "status": "reviewed"
}
```

### `POST /api/corridors/analyze`

- Request:

```json
{
  "roadId": "road_20000641"
}
```

- Response:

```json
{
  "corridorId": "cor_road_20000641",
  "roadId": "road_20000641",
  "name": "BROADWAY",
  "knownCurbRamps": 2,
  "possibleMissingCurbCuts": 2,
  "hydrantsNearby": 1,
  "bikeLanesNearby": 1,
  "userAnnotationsNearby": 1,
  "busStopsNearby": 0,
  "parkingConflicts": 0,
  "bikeLaneFeasibility": "Medium",
  "planningNotes": [
    "Possible missing curb cuts near the selected corridor should be field-checked."
  ]
}
```

### `POST /api/reports/corridor`

- Accepts `corridor_id`, `road_id`, or `roadId`
- Request:

```json
{
  "corridor_id": "road_20000641",
  "format": "html"
}
```

- Response:

```json
{
  "reportId": "rep_001",
  "roadId": "road_20000641",
  "downloadUrl": "/api/reports/rep_001/download",
  "summary": "BROADWAY corridor report queued successfully. Export includes counts and planning notes."
}
```

### `GET /api/reports/{reportId}/download`

- Purpose: download the generated HTML report
