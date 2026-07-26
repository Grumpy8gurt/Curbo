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
- `cd frontend && npm audit`
- `python scripts/validate_geojson.py`
- `python scripts/fetch_eugene_data.py` (offline/cache-preservation path)
- `docker compose config`

The final repository review produced 17 passing backend tests, a successful frontend production build, zero reported npm vulnerabilities, 7 valid GeoJSON files, a successful cache-only refresh check, and valid default and optional-database Compose configurations. The frontend build reports only Vite's existing large-chunk advisory for the MapLibre bundle. This is not a build failure. A Docker runtime check could not connect because Docker Desktop/the local daemon was not running.

### Sprint 3 Issues Discovered and Resolved

| Issue discovered | Resolution | Verification |
|---|---|---|
| The frontend annotation request used an underscored type that the backend rejected with HTTP 422. | Send the documented `annotationType`, latitude, and longitude contract. | Browser creation succeeded and the record survived a backend restart. |
| Map data could arrive before the MapLibre style finished loading, leaving sources empty. | Track map readiness and synchronize source data after the load event. | Browser verification showed loaded layer counts and working feature/corridor interactions. |
| Eugene bikeway data includes `MultiLineString` features. | Add backend and frontend geometry support plus bbox handling for both line types. | Layer tests and the production TypeScript build passed. |
| A broad `models/` ignore rule excluded required SQLAlchemy modules from repository history. | Scope artifact ignores to repository-root directories and track `backend/app/models/`. | A tracked-files audit and clean-tree test run confirmed the runtime package is complete. |
| Local services started in subdirectories and did not consistently discover the root `.env` file. | Configure FastAPI settings and Vite to read the repository-root environment file. | Backend tests and the frontend production build passed with the shared configuration. |
| The clean-clone npm audit reported three vulnerabilities in the older Vite development toolchain. | Upgrade Vite and its React plugin to current releases. | The production build passed and `npm audit` reported zero vulnerabilities. |
| API fallback logic could hide reachable-backend HTTP errors behind synthetic local data. | Restrict fallback behavior to network failures and surface HTTP errors in the dashboard. | Invalid annotations return HTTP 422, while normal offline fallback remains available. |
| Generated reports had no usable frontend download control and were not persisted by Compose. | Add a backend-aware download link and a named report volume. | Browser report generation exposed the HTML download and backend download tests passed. |
| Bounding-box filtering only matched line vertices and accepted reversed bounds. | Add segment/rectangle intersection and ordered-bound validation. | Crossing-line and reversed-bound tests passed. |
| Corrupt annotation JSON silently restored seed data. | Fail startup with a clear path-specific error without overwriting the file. | Corruption-preservation and restart-persistence tests passed. |
| The first manual server commands inherited the wrong shell working directory. | Use explicit `cd backend` and `cd frontend` commands, matching the README. | Both services subsequently started and completed browser verification. |

### Remaining Limitations

- The JSON annotation store is designed for a single-user prototype and does not provide concurrent-write coordination.
- Eugene layers are committed extracts; a refresh may produce larger files as the public services change.
- PostGIS is optional scaffolding; SQLAlchemy initializes only when `DATABASE_URL` is configured.
- Full Docker runtime startup still requires a local Docker daemon; Compose configuration itself validates.
