# API Contract

This document reflects the verified CURBO Sprint 5 integration contract.

The canonical data API prefix is `/api/v1`. The older `/api` paths remain temporarily available for earlier-client compatibility but are omitted from OpenAPI. When `AUTH_REQUIRED=true`, every data route requires `X-API-Key`. Health routes remain public for platform probes. Production annotation creates also require an `Idempotency-Key` header between 8 and 128 characters.

## Backend Routes

### `GET /api/health`

```json
{
  "status": "ok",
  "service": "curbo-backend"
}
```

`GET /api/live` checks only the process. `GET /api/ready` and `/api/health` return HTTP 503 when a configured database is unavailable.

### `GET /api/v1/layers/roads`

- Response: GeoJSON `FeatureCollection`
- Road ids use the normalized Eugene shape, for example `road_20000641`

### `GET /api/v1/layers/sidewalk-ramps`

- Response: GeoJSON `FeatureCollection`
- Available normalized measurements use `width_feet`,
  `left_width_feet`, `right_width_feet`, `grade_percent`,
  `left_grade_percent`, `right_grade_percent`,
  `cross_slope_percent`, `left_cross_slope_percent`, and
  `right_cross_slope_percent`. Values may be null when the City source does
  not publish a measurement. Nonpositive physical-width sentinels normalize to
  null; valid 0% slope measurements remain available.

### `GET /api/v1/layers/curb-ramps`

- Compatibility alias for `/api/v1/layers/sidewalk-ramps`

### `GET /api/v1/layers/hydrants`

- Response: GeoJSON `FeatureCollection`

### `GET /api/v1/layers/bike-lanes`

- Response: GeoJSON `FeatureCollection` containing `LineString` or `MultiLineString` features

### `GET /api/v1/layers/annotations`

- Response: GeoJSON `FeatureCollection`

All infrastructure layer routes accept an optional
`bbox=minLng,minLat,maxLng,maxLat` query. Bounds must be finite and ordered;
points or line segments intersecting the box are returned.

### `GET /api/v1/annotations`

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
      "id": "ann_9f347dc8088245d9b39aaf6984ddc874",
      "properties": {
        "annotation_id": "ann_9f347dc8088245d9b39aaf6984ddc874",
        "annotation_type": "missing curb cut",
        "description": "Northwest corner slope feels absent during field review.",
        "status": "pending",
        "source": "authenticated reviewer",
        "created_at": "2026-07-05T15:00:00+00:00",
        "version": 1
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-123.0894, 44.0519]
      }
    }
  ]
}
```

### `POST /api/v1/annotations`

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
- LineStrings are limited to 1,000 positions. The client cannot set `source`.
- Retrying with the same `Idempotency-Key` returns the original annotation instead of creating a duplicate.
- Response: one annotation `Feature`

### `PATCH /api/v1/annotations/{annotation_id}`

- Purpose: persist a user-selected review state from the map popup
- Supported states: `pending`, `reviewed`, `confirmed`, and `rejected`
- Request:

```json
{
  "status": "reviewed",
  "expectedVersion": 1
}
```

Successful updates increment `version`. A stale `expectedVersion` or invalid lifecycle transition returns HTTP 409.

### `POST /api/v1/corridors/analyze`

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
  "possibleMissingCurbCuts": 0,
  "hydrantsNearby": 1,
  "bikeLanesNearby": 1,
  "userAnnotationsNearby": 1,
  "busStopsNearby": 0,
  "parkingConflicts": 1,
  "bikeLaneGaps": 0,
  "intersectionSafetyConcerns": 0,
  "annotationsNeedingReview": 0,
  "bikeLaneFeasibility": "Medium",
  "reviewPriority": "Low",
  "reviewSignals": [
    "1 active parking/loading conflict near the corridor."
  ],
  "dataLimitation": "Screening only: CURBO uses cached infrastructure and reviewer observations; it does not include current crash, speed, traffic-volume, exposure, parking, or right-of-way data and does not rank projects or determine compliance.",
  "planningNotes": [
    "Parking conflicts should be reviewed before committing to curb changes."
  ]
}
```

`userAnnotationsNearby` is a historical count and includes rejected notes.
Concern fields and review attention exclude annotations whose status is
`rejected`. `annotationsNeedingReview` counts active `pending` notes. The
Low/Medium/High review-attention heuristic is documented in
`docs/planning-review-rationale.md`; it is not a safety or project score.

### `POST /api/v1/reports/corridor`

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
  "reportId": "rep_7e687908aef5498d85c0e403971ac5bb",
  "roadId": "road_20000641",
  "downloadUrl": "/api/v1/reports/rep_7e687908aef5498d85c0e403971ac5bb/download",
  "summary": "BROADWAY corridor report generated successfully. Export includes Eugene layer counts, planning notes, and annotation status."
}
```

Only `html` is accepted. Report identifiers are collision-resistant and database-backed report downloads survive application restarts.

### `GET /api/v1/reports/{reportId}/download`

- Purpose: download the generated HTML report
