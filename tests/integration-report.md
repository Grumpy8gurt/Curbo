# CURBO Sprint 3 Integration Report

## Summary

- Repository structure and frontend/backend separation: pass
- Backend tests: 20 passed
- Frontend production build: pass
- Frontend dependency audit: zero reported vulnerabilities
- GeoJSON validation: 7 files passed
- Cache-only refresh behavior: pass
- Docker Compose configuration: pass
- Browser verification of layers, annotations, corridors, reports, and road labels: pass
- Docker runtime startup: blocked because the local Docker daemon was unavailable

## Sprint 3 Evolution

The current branch was reviewed against the previous prototype branch. Sprint 3 makes the following meaningful changes:

- Renames the active product to CURBO.
- Removes the ML service, image upload, curb-cut detection routes, model dependencies, detection types, and review panels.
- Replaces mock-first infrastructure loading with cached City of Eugene GIS data normalized by `EugeneDataService`.
- Adds roads, sidewalk ramps, fire hydrants, and bicycle-facility API layers, including bounding-box filtering.
- Expands the road cache to all 13,520 published street segments and renders directional street names with locally cached MapLibre glyphs.
- Adds JSON-file annotation persistence that survives backend restarts and fails clearly on corrupt storage.
- Keeps PostgreSQL/PostGIS as optional future scaffolding instead of a runtime requirement.
- Adds corridor analysis using nearby ramps, hydrants, bicycle facilities, and annotations.
- Adds downloadable HTML corridor reports and persistent Docker report storage.
- Adds GeoJSON refresh and validation scripts.
- Improves frontend API error handling while retaining network-failure fallback data.
- Adds tests for Eugene data normalization, persistence, coordinate validation, line intersection, and `MultiLineString` behavior.

## Verification Commands

```bash
cd backend && pytest
cd frontend && npm run build
cd frontend && npm audit
python scripts/validate_geojson.py
EUGENE_CACHE_ONLY=true python scripts/fetch_eugene_data.py --layer roads
docker compose config
docker compose --profile database config
```

## Observed Behavior

- `GET /api/health` returns HTTP 200 with `status: ok`.
- Infrastructure endpoints return normalized GeoJSON with cache metadata.
- `GET /api/layers/roads` returns 13,520 uniquely identified street segments.
- The map displays collision-aware street labels following road geometry.
- Annotation creation updates the map and persists to the configured JSON file.
- Corridor selection returns nearby infrastructure counts and planning notes.
- Report generation exposes a downloadable HTML report.
- No active ML, image-upload, model-confidence, or detection-review workflow remains.

## Remaining Limitations

- The annotation store is appropriate for a single-user prototype, not concurrent production writes.
- Roads are a complete dated service snapshot; other Eugene infrastructure layers remain bounded extracts.
- The MapLibre production bundle triggers a non-blocking large-chunk advisory.
- Backend tests emit a non-blocking Starlette/httpx deprecation warning.
- Full Docker runtime startup still requires verification on a machine with a running Docker daemon.
