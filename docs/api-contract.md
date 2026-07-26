# API Contract

This document reflects the verified CURBO Sprint 3 integration contract.

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
  "annotationType": "missing curb cut",
  "description": "Potential curb issue at the corner.",
  "latitude": 44.0515,
  "longitude": -123.091
}
```

- Response: one annotation `Feature`

### `PATCH /api/annotations/{annotation_id}`

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
