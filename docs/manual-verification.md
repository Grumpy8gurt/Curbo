# Sprint 2 Manual Verification

## Actions Performed

1. Reviewed the repository structure, sample GeoJSON, and Sprint 2 documentation files.
2. Built the frontend with `cd frontend && npm run build`.
3. Ran backend tests with `cd backend && pytest`.
4. Started the backend locally with `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
5. Performed targeted backend smoke checks for:
   - `GET /api/health`
   - `GET /api/layers/roads`
   - `POST /api/annotations`
   - `POST /api/reports/corridor`
   - `GET /api/reports/{report_id}/download`
6. Loaded the frontend locally and confirmed that the MapLibre canvas rendered after replacing the remote demo basemap dependency with a local style.
7. Validated Docker Compose syntax with `docker compose config`.
8. Investigated the previous Docker startup failure and traced it to the backend container missing the sample data directory needed at startup.

## Expected Results

- The frontend should build without TypeScript errors.
- The backend should start, pass tests, and expose the main MVP routes.
- The frontend should render a working map view instead of a blank panel.
- Docker Compose should parse successfully, and the backend container should have access to the sample GeoJSON files it needs at startup.

## Observed Results

- Frontend build succeeded.
- Backend tests succeeded.
- Local backend startup succeeded.
- Backend smoke checks returned successful responses for the tested MVP routes.
- The frontend rendered a live MapLibre canvas locally after the basemap fix.
- Docker Compose configuration parsed successfully.
- The earlier Docker backend crash was consistent with the backend image not including `data/sample`; the compose and Dockerfile configuration were updated to address that path issue.

## Issues Found

- The application is still mock-first. Roads, curb ramps, hydrants, annotations, and reports are not yet fully persisted through a production-style database workflow.
- Docker runtime behavior still needs one more full end-to-end verification on a machine with Docker Desktop or a running Docker daemon after the backend image fix.
- The frontend production bundle is still fairly large because MapLibre is included in the main bundle.

## Engineering Conclusion

The Sprint 2 prototype now demonstrates a complete, explainable feature slice: the frontend can load map data, a user can interact with the map, the backend can return GeoJSON and corridor analysis, and reports can be generated and downloaded. The biggest remaining work is not basic wiring anymore; it is scope control, persistent data, and one more end-to-end Docker verification after the image-path fix.

## Sprint 3 Manual Verification

Sprint 2 results above are retained as historical evidence. Sprint 3 verification targets the Eugene GIS cache, API-first frontend, persistent annotations, and removal of the active ML workflow.

| Test | Expected Result | Observed Result | Status |
|---|---|---|---|
| App starts locally | Backend and frontend start without an ML service | Backend and frontend started on ports 8000 and 5173 | Pass |
| Backend health endpoint returns OK | `GET /api/health` returns HTTP 200 and `status: ok` | Health response returned HTTP 200 with `status: ok` | Pass |
| Eugene roads layer loads | Roads endpoint returns a non-empty FeatureCollection | Cached, normalized Eugene roads returned | Pass |
| Sidewalk ramps layer loads | Sidewalk-ramp endpoint and curb-ramp alias return points | Both endpoints returned the same non-empty point layer | Pass |
| Hydrants layer loads | Hydrants endpoint returns a non-empty FeatureCollection | Cached, normalized Eugene hydrants returned | Pass |
| Bike lanes layer loads or reports status | Bike-lane endpoint returns data or an explicit unavailable status | Cached Eugene bicycle facilities returned | Pass |
| User can create an annotation | POST creates a feature and writes the JSON store | Annotation appeared through the API and persisted to the configured file | Pass |
| Annotation appears in frontend | Newly created annotation is added to map state | Annotation marker appeared after form submission | Pass |
| Corridor summary displays | Selecting a road shows nearby ramps, hydrants, bike data, and annotations | Corridor panel populated from backend analysis | Pass |
| ML/image detection UI is no longer active | No upload, model confidence, or detection-review controls appear | No active ML or image-detection UI is present | Pass |
| README instructions are accurate | Documented run, build, fetch, and validation commands work | Commands were executed as documented | Pass |

### Sprint 3 Automated Checks

- `cd backend && pytest`
- `cd frontend && npm run build`
- `python scripts/validate_geojson.py`
- `python scripts/fetch_eugene_data.py` (offline/cache-preservation path)
- `docker compose config`

The frontend build reports only Vite's existing large-chunk advisory for the MapLibre bundle. This is not a build failure. Full Docker runtime startup remains dependent on a locally running Docker daemon.
