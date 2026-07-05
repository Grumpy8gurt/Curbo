# API Contract

This document reflects the current MVP integration contract. The frontend’s existing fetch layer is treated as the canonical client contract, and the backend now implements that shape directly.

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
  "knownCurbRamps": 3,
  "possibleMissingCurbCuts": 3,
  "hydrantsNearby": 1,
  "busStopsNearby": 1,
  "parkingConflicts": 2,
  "bikeLaneFeasibility": "Medium",
  "planningNotes": [
    "Possible missing curb cuts near the selected corridor should be field-checked."
  ]
}
```

### `POST /api/uploads/images`

- Request: `multipart/form-data` with field `image`
- Response:

```json
{
  "uploadId": "upl_001",
  "filename": "street-view.jpg",
  "status": "stored"
}
```

### `GET /api/detection/curb-cuts`

- Purpose: return all detections as a map-ready GeoJSON `FeatureCollection`

### `POST /api/detection/curb-cuts`

- Request:

```json
{
  "upload_id": "upl_001"
}
```

- Response:

```json
{
  "type": "Feature",
  "id": "det_003",
  "properties": {
    "detection_id": "det_003",
    "label": "Possible Curb Cut",
    "confidence": 0.72,
    "review_status": "pending",
    "upload_id": "upl_001",
    "source": "mock-v0.1",
    "bbox": [96, 72, 232, 188]
  },
  "geometry": {
    "type": "Point",
    "coordinates": [-123.0868, 44.0521]
  }
}
```

### `PATCH /api/detections/{detection_id}`

- Request:

```json
{
  "review_status": "confirmed"
}
```

- Response: one detection `Feature`

### `POST /api/reports/corridor`

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
  "summary": "Willamette Street corridor report queued successfully. Mock export includes counts, notes, and detection review status."
}
```

### `GET /api/reports/{reportId}/download`

- Purpose: download the generated HTML report

## ML Routes

### `GET /health`

```json
{
  "status": "ok",
  "service": "curbo-ml"
}
```

### `POST /detect`

- Request: `multipart/form-data` with `file` plus optional `image_id`, `latitude`, `longitude`, `road_id`, and `source`
- Response:

```json
{
  "image_id": "upl_001",
  "model_version": "mock-v0.1",
  "detections": [
    {
      "label": "possible_curb_cut",
      "confidence": 0.72,
      "bbox": [96, 72, 232, 188],
      "estimated_location": {
        "type": "Point",
        "coordinates": [-123.0868, 44.0521]
      },
      "review_status": "pending"
    }
  ]
}
```
