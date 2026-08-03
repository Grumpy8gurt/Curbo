# CURBO Architecture Overview

## Sprint 4 Evolution

Sprint 4 keeps the existing React, FastAPI, and atomic JSON persistence
boundaries. It completes the frontend path to the existing annotation PATCH
endpoint and extends Eugene sidewalk-ramp normalization so published
measurements reach the inspection popup. No new service or database
responsibility was introduced.

## Sprint 3 Evolution

Sprint 3 evolves the existing React/MapLibre frontend, FastAPI routes, sample GeoJSON layers, annotations, corridor summaries, and HTML reports. It replaces the mock-first layer path with normalized, cached City of Eugene GIS data and removes the active ML and image-upload architecture.

## Runtime Architecture

```text
City of Eugene ArcGIS query URLs (optional refresh)
  -> scripts/fetch_eugene_data.py
  -> data/eugene/*.geojson (committed offline cache)
  -> EugeneDataService normalization
  -> FastAPI /api/layers/* and corridor analysis
  -> React + TypeScript + MapLibre dashboard

Frontend API failure
  -> compact local TypeScript fallback data

POST /api/annotations
  -> AppStore
  -> backend/data/annotations.json

PATCH /api/annotations/{annotation_id}
  -> AppStore status update
  -> backend/data/annotations.json

Eugene sidewalk-ramp dimensions
  -> EugeneDataService normalization
  -> curb-ramp Feature properties
  -> selected-feature popup
```

PostgreSQL/PostGIS remains available through the optional Docker `database` profile. SQLAlchemy initializes only when `DATABASE_URL` is explicitly configured; the Sprint 3 runtime does not require a database or import the Eugene cache into PostGIS.

## Frontend Responsibilities

- Center the planning map on Eugene, Oregon.
- Render roads, line-following street names, sidewalk ramps, fire hydrants, bike facilities, and annotations.
- Show feature counts and a clear unavailable state for empty layers.
- Use backend APIs by default and compact local fallbacks only when the API cannot be reached; surface HTTP errors in the UI.
- Support point and line annotation creation, persistent status review, and corridor selection without ML-oriented UI.
- Display curb-ramp width, grade, and cross-slope values with source units when available.

## Backend Responsibilities

- Serve stable, validated GeoJSON FeatureCollections under `/api`.
- Keep `/api/layers/curb-ramps` as an alias for `/api/layers/sidewalk-ramps`.
- Normalize source-specific Eugene fields into frontend-facing properties.
- Filter layers by optional bounding box and calculate lightweight corridor metrics.
- Persist annotation creation and status updates and generate simple HTML corridor reports.
- Reject explicit GeoJSON positions outside valid longitude/latitude ranges.

## Data Layer Responsibilities

- `data/eugene/` is the normal runtime source. The road cache contains the complete service snapshot; the other infrastructure layers remain bounded demonstration extracts.
- `data/sample/` is retained as a compact backend fallback from the earlier prototype.
- `scripts/fetch_eugene_data.py` performs an optional, API-key-free cache refresh from configured URLs.
- Selective refreshes such as `--layer roads` avoid replacing unrelated cached layers.
- `scripts/validate_geojson.py` validates both Eugene and sample datasets.
- The application never requires a live external GIS service at startup.
- Street labels use a locally cached MapLibre glyph range so they remain available in the offline demo.

## Persistence Choice

Sprint 3 uses an atomic JSON-file write for user annotations at `backend/data/annotations.json`. This is intentionally lightweight, easy to inspect, and sufficient for a single-user prototype. Docker mounts named volumes for annotations and generated HTML reports. PostgreSQL/PostGIS remains a future migration path rather than a Sprint 3 requirement.

## Removed ML Responsibility

The ML service, image-upload path, detection endpoints, model dependencies, map layer, and review UI are not part of the active architecture. This is a deliberate scope decision: Sprint 3 focuses on civic GIS integration and clearer frontend/backend boundaries.

## Remaining Architectural Questions

- Whether Eugene layers should eventually be imported into PostGIS for indexed spatial queries.
- Whether annotation persistence should move from JSON to PostgreSQL for concurrent users.
- Which public GIS service URLs and refresh cadence should be treated as production sources.
- Whether a hosted basemap and server-side map tiles are needed for larger datasets.
- How authentication, data provenance, and dataset licensing should be handled before deployment.
