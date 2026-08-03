# Sprint 4 Manual Verification

Sprint 4 verification focused on user input and its effects: annotation
creation, status review, geometry rejection, persistence, and curb-ramp
measurement display.

| Test | Expected Result | Observed Result | Status |
|---|---|---|---|
| Load the connected application | Cached Eugene layers and persistent annotations load | Browser loaded 13,520 roads, 400 sidewalk ramps, 400 hydrants, 400 bike facilities, and the annotation layer | Pass |
| Create a curb-cut annotation with manual coordinates | A pending annotation is persisted, added to map state, and selected | Browser displayed “New annotation added to the map,” increased the annotation count, and opened the new pending annotation | Pass |
| Change the selected annotation to reviewed | PATCH persists the status and the popup updates without a reload | Browser displayed “Annotation status updated to reviewed” and the control changed to `reviewed` | Pass |
| Reject invalid explicit GeoJSON | Out-of-range point and line coordinates return HTTP 422 | Automated API tests rejected longitude 999 and latitude 999 | Pass |
| Preserve curb-ramp measurements | Eugene widths and cross slopes survive normalization and render with units | Normalizer and popup tests displayed `4.9 ft` and `1.1 %` values | Pass |
| Verify after frontend state refactoring | Status changes still update API state and selected-feature state | Component/API tests passed and the production TypeScript build succeeded | Pass |

### Sprint 4 Automated Checks

- `cd backend && pytest` — 23 passed
- `cd frontend && npm test` — 3 passed
- `cd frontend && npm run build` — passed
- `cd frontend && npm audit` — zero vulnerabilities
- `python scripts/validate_geojson.py` — 7 valid files
- `docker compose config` — valid configuration

### Sprint 4 Defects Discovered and Resolved

| Defect | Resolution | Verification |
|---|---|---|
| The backend status PATCH existed but had no user-facing control. | Add a review-status selector, PATCH client, fallback update, and local state synchronization. | Browser create/review workflow plus frontend component and API tests passed. |
| Explicit GeoJSON coordinates bypassed longitude/latitude range checks. | Share finite/range validation across Point and every LineString position. | Both invalid explicit geometry cases return HTTP 422. |
| Eugene curb-ramp measurements were discarded during normalization. | Preserve aggregate and left/right width and slope fields and display available values with units. | Backend normalization and frontend rendering tests passed. |
| The frontend had no automated test runner. | Add Vitest, jsdom, and Testing Library with focused user-effect tests. | Three frontend tests pass in CI-style run mode. |
| Annotation descriptions could exceed the backend limit before submission. | Add the matching 2,000-character limit to the textarea. | TypeScript build and component behavior remained valid. |

### Remaining Limitations

- Dimension availability depends on the City of Eugene source; null values are omitted rather than inferred.
- The JSON annotation store remains a single-user prototype without concurrent-write coordination.
- Delete and geometry editing are intentionally outside this narrowly scoped capability.
- Authentication and authorization remain required before production deployment.

---

## Sprint 3 Manual Verification

This verification targets the Eugene GIS cache, API-first frontend, persistent annotations, complete labeled road layer, and removal of the active ML workflow.

| Test | Expected Result | Observed Result | Status |
|---|---|---|---|
| App starts locally | Backend and frontend start without an ML service | Backend and frontend started on ports 8000 and 5173 | Pass |
| Backend health endpoint returns OK | `GET /api/health` returns HTTP 200 and `status: ok` | Health response returned HTTP 200 with `status: ok` | Pass |
| Eugene roads layer loads | Roads endpoint returns the complete cached service snapshot | 13,520 cached, normalized Eugene street segments returned | Pass |
| Street names render on roads | Named roads display collision-aware labels following their line geometry | MapLibre loaded the cached local glyph range and rendered the road-label symbol layer | Pass |
| Sidewalk ramps layer loads | Sidewalk-ramp endpoint and curb-ramp alias return points | Both endpoints returned the same non-empty point layer | Pass |
| Hydrants layer loads | Hydrants endpoint returns a non-empty FeatureCollection | Cached, normalized Eugene hydrants returned | Pass |
| Bike lanes layer loads or reports status | Bike-lane endpoint returns data or an explicit unavailable status | Cached Eugene bicycle facilities returned | Pass |
| User can create an annotation | POST creates a feature and writes the JSON store | Annotation appeared through the API and persisted to the configured file | Pass |
| User can draw a line annotation | POST accepts valid GeoJSON `LineString` reviewer geometry | Line annotation creation and minimum-position validation tests passed | Pass |
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

The final repository review produced 20 passing backend tests, a successful frontend production build, zero reported npm vulnerabilities, 7 valid GeoJSON files, a successful cache-only refresh check, and valid default and optional-database Compose configurations. The frontend build reports only Vite's existing large-chunk advisory for the MapLibre bundle. This is not a build failure. A Docker runtime check could not connect because Docker Desktop/the local daemon was not running.

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
| The committed road cache contained only 400 Eugene street segments and the map did not label them. | Refresh all 13,520 published segments, retain unique `OBJECTID` values, normalize directional names, and add a line-following MapLibre label layer with local glyphs. | The API returned 13,520 uniquely identified roads, browser verification loaded the label resource, GeoJSON validation passed, and the frontend build succeeded. |

### Remaining Limitations

- The JSON annotation store is designed for a single-user prototype and does not provide concurrent-write coordination.
- Eugene data is a dated cache: roads contain the complete July 27, 2026 service snapshot, while the other infrastructure layers remain bounded extracts.
- PostGIS is optional scaffolding; SQLAlchemy initializes only when `DATABASE_URL` is configured.
- Full Docker runtime startup still requires a local Docker daemon; Compose configuration itself validates.
