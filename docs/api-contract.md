# API Contract

This document reflects the current verified MVP integration contract.

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
- Road ids use the sample-data shape, for example `rd_001`

### `GET /api/layers/curb-ramps`

- Response: GeoJSON `FeatureCollection`

### `GET /api/layers/hydrants`

- Response: GeoJSON `FeatureCollection`

### `GET /api/layers/annotations`

- Response: GeoJSON `FeatureCollection`

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
  "roadId": "rd_001"
}
```

- Response:

```json
{
  "corridorId": "cor_rd_001",
  "roadId": "rd_001",
  "name": "Willamette Street",
  "knownCurbRamps": 2,
  "possibleMissingCurbCuts": 2,
  "hydrantsNearby": 1,
  "busStopsNearby": 1,
  "parkingConflicts": 2,
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
  "corridor_id": "rd_001",
  "format": "html"
}
```

- Response:

```json
{
  "reportId": "rep_001",
  "roadId": "rd_001",
  "downloadUrl": "/api/reports/rep_001/download",
  "summary": "Willamette Street corridor report queued successfully. Mock export includes counts and planning notes."
}
```

### `GET /api/reports/{reportId}/download`

- Purpose: download the generated HTML report
