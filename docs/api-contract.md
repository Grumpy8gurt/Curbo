# Planned API Contract

This document defines the intended interface for the initial backend. These endpoints are planned only and are not implemented yet.

## `GET /api/health`

- Purpose: Confirm backend availability and basic dependency readiness.
- Request shape: No body.
- Response shape:

```json
{
  "status": "ok",
  "service": "backend",
  "version": "0.1.0"
}
```

## `GET /api/layers/roads`

- Purpose: Return road centerline data as GeoJSON.
- Request shape: Optional query params for bbox, corridor id, or pagination later.
- Response shape:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

## `GET /api/layers/curb-ramps`

- Purpose: Return curb ramp point features as GeoJSON.
- Request shape: Optional query params for bbox, status, or corridor filters later.
- Response shape:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

## `GET /api/layers/hydrants`

- Purpose: Return hydrant point features for map display and proximity analysis.
- Request shape: Optional query params for bbox or corridor filters later.
- Response shape:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

## `GET /api/annotations`

- Purpose: List user-created annotations for map display.
- Request shape: Optional query params for bbox, author, annotation type, or corridor.
- Response shape:

```json
{
  "items": [
    {
      "id": "ann_123",
      "type": "note",
      "geometry": {
        "type": "Point",
        "coordinates": [-123.0, 44.0]
      },
      "properties": {
        "title": "Example annotation",
        "description": "Planner note"
      }
    }
  ]
}
```

## `POST /api/annotations`

- Purpose: Create a new annotation tied to a point, line, or polygon geometry.
- Request shape:

```json
{
  "type": "note",
  "geometry": {
    "type": "Point",
    "coordinates": [-123.0, 44.0]
  },
  "properties": {
    "title": "Missing ramp",
    "description": "Needs field review"
  }
}
```

- Response shape:

```json
{
  "id": "ann_123",
  "created_at": "2026-06-29T00:00:00Z"
}
```

## `POST /api/corridors/analyze`

- Purpose: Run a corridor summary analysis across one or more selected geometries.
- Request shape:

```json
{
  "name": "Downtown segment",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-123.091, 44.051],
      [-123.085, 44.053]
    ]
  },
  "buffer_meters": 25
}
```

- Response shape:

```json
{
  "corridor_id": "cor_123",
  "summary": {
    "road_segments": 0,
    "curb_ramps": 0,
    "hydrants": 0
  }
}
```

## `POST /api/uploads/images`

- Purpose: Accept image uploads for future detection or manual review workflows.
- Request shape: `multipart/form-data` with image file plus optional metadata fields.
- Response shape:

```json
{
  "upload_id": "upl_123",
  "filename": "street-view.jpg",
  "status": "stored"
}
```

## `POST /api/detection/curb-cuts`

- Purpose: Trigger curb-cut detection on an uploaded image or referenced image set.
- Request shape:

```json
{
  "upload_id": "upl_123",
  "mode": "mock"
}
```

- Response shape:

```json
{
  "detection_id": "det_123",
  "status": "queued",
  "mode": "mock"
}
```

## `POST /api/reports/corridor`

- Purpose: Generate or queue a corridor report artifact.
- Request shape:

```json
{
  "corridor_id": "cor_123",
  "format": "html"
}
```

- Response shape:

```json
{
  "report_id": "rep_123",
  "status": "queued",
  "format": "html"
}
```
