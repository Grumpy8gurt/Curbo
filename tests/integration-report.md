# Curb Goblin 3000 Integration Report

## Summary

- Repo structure: pass
- Sample GeoJSON validation: pass
- Frontend build: pass
- Backend tests: pass
- Backend startup command: pass
- ML tests: pass
- ML startup command: pass
- Docker Compose config validation: pass
- Docker Compose runtime startup: blocked by local Docker daemon not running

## Repo Structure

Verified required top-level items:

- `README.md`
- `docker-compose.yml`
- `.env.example`
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/data-model.md`
- `docs/agent-responsibilities.md`
- `frontend/`
- `backend/`
- `ml/`
- `data/sample/`
- `scripts/setup.sh`

The main repo shape is coherent and now includes runnable frontend, backend, and ML directories.

## Frontend

Checks run:

- `cd frontend && npm run build`

Result:

- Build passes without TypeScript errors.
- The app still defaults to mock mode, but the live API adapter layer now tolerates the backend's current request and response shapes.

Issues found and fixed:

- Real API adapters did not match backend upload, annotation, corridor, report, and detection payloads.
- Detection update route naming drifted between singular and plural forms.
- One TypeScript issue used `replaceAll`, which is not available under the current compiler target assumptions.
- Frontend README instructions were updated to document live backend mode more accurately.

## Backend

Checks run:

- `cd backend && pytest`
- `cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Lifespan-enabled TestClient smoke checks for health, layers, annotation create, upload, detection, detection patch, report create, and report download

Result:

- `pytest` passes: 9 tests passed.
- `uvicorn` startup now succeeds.
- Health, layer, upload, detection, corridor, and report flows all responded successfully in smoke checks.

Issues found and fixed:

- Backend `uvicorn` startup originally failed because schema exports had drifted and no longer matched the package import surface.
- Detection route compatibility needed to support both singular and plural patch endpoints.
- README contract notes were partly stale and were updated.

## ML Layer

Checks run:

- `cd ml && pytest`
- `cd ml && uvicorn app.main:app --host 127.0.0.1 --port 9000`
- TestClient smoke checks for `/health` and `/detect`

Result:

- `pytest` passes: 4 tests passed.
- `uvicorn` startup succeeds.
- `/detect` returns the expected mock detection shape with `label`, `confidence`, `bbox`, `estimated_location`, and `review_status`.

Issues found and fixes made:

- The ML folder was missing a runnable service implementation in the repo workflow.
- A minimal FastAPI mock ML service, requirements file, Dockerfile, and startup README were added.
- The service was aligned to the pre-existing tests already present in `ml/tests/`.

## Docker

Checks run:

- `docker compose config`
- `docker compose up -d postgres`
- `docker compose ps`

Result:

- `docker compose config` passes.
- Runtime startup could not be completed because the local Docker daemon was not running in this environment.

Notes:

- The compose file now includes verified build contexts for `backend` and `ml`.
- Postgres remains the only required service for the documented MVP compose workflow.

## API Contract Alignment

Frontend and backend alignment after fixes:

- Annotation create/list flows are now compatible with backend feature-shaped responses.
- Upload handling now accepts the backend's `uploadId` response.
- Detection update supports both `PATCH /api/detection/{id}` and `PATCH /api/detections/{id}`.
- Corridor analysis and report adapters now accept the backend's current camelCase responses while remaining tolerant of earlier draft shapes.

Backend and ML alignment:

- Backend detection service is configured to call `ML_SERVICE_URL`, defaulting to `http://localhost:9000/detect`.
- ML `/detect` response includes `confidence`, `bbox`, `estimated_location`, and `review_status`.
- Backend can fall back to local mock detection if ML is unavailable.

## Data Validation

Validated:

- `data/sample/roads.sample.geojson`
- `data/sample/curb_ramps.sample.geojson`
- `data/sample/hydrants.sample.geojson`

Results:

- All files are valid JSON.
- All files are GeoJSON `FeatureCollection` objects with `Feature` entries, `geometry`, and `properties`.
- Coordinates are plausibly near Eugene, Oregon.

## Remaining Risks

- Docker runtime was not available here, so full compose startup remains unverified until Docker Desktop or the daemon is running locally.
- Frontend still defaults to mock mode, so developers must set `VITE_USE_MOCK_API=false` to exercise the live backend manually.
- The frontend production bundle is large because MapLibre ships in the main chunk.
- Backend and ML tests emit a `fastapi.testclient` deprecation warning tied to the installed `httpx`/Starlette combination.
- There is still no browser-level end-to-end test covering frontend plus live backend plus ML together.

## Recommended Next Steps

- Start Docker locally and rerun `docker compose up -d postgres` plus `docker compose ps`.
- Run the frontend with `VITE_USE_MOCK_API=false` against the live backend and manually verify upload, detection review, and report download in the browser.
- Add one end-to-end smoke test that covers backend plus ML plus a representative frontend flow.
- Decide when to switch the frontend default from mock mode to live backend mode.
- Replace in-memory backend stores with persistent database-backed implementations when the MVP moves past local demo mode.
