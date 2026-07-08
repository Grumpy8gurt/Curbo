# Sprint 2 Manual Verification

## Actions Performed

1. Reviewed the repository structure to confirm the expected Sprint 2 folders and core files exist.
2. Validated the sample GeoJSON files in `data/sample/`.
3. Built the frontend with `cd frontend && npm run build`.
4. Ran backend tests with `cd backend && pytest`.
5. Started the backend with `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
6. Ran backend smoke checks for:
   - `GET /api/health`
   - `GET /api/layers/roads`
   - `POST /api/annotations`
   - `POST /api/uploads/images`
   - `POST /api/detection/curb-cuts`
   - `PATCH /api/detection/{detection_id}`
   - `POST /api/reports/corridor`
   - `GET /api/reports/{report_id}/download`
7. Validated Docker Compose syntax with `docker compose config`.
8. Attempted `docker compose up -d postgres` and `docker compose ps`.
9. Visited site at local host 127.0.0.1

## Expected Results

- The frontend should build without TypeScript errors.
- The backend should start, pass tests, and expose working MVP routes.
- The ML service should start, pass tests, and return a mock detection response.
- The sample GeoJSON files should be valid FeatureCollections.
- Docker Compose should at minimum parse successfully.
- If Docker is available locally, Postgres should start from Compose.

## Observed Results

- Frontend build succeeded.
- Backend tests succeeded: 9 tests passed.
- Backend startup succeeded after small integration fixes.
- Backend smoke checks returned successful responses for health, layers, annotation creation, upload, detection, detection update, report creation, and report download.
- ML `/detect` returned mock detection data with `label`, `confidence`, `bbox`, `estimated_location`, and `review_status`.
- Sample GeoJSON validation succeeded.
- `docker compose config` succeeded.
- Docker runtime startup could not be fully verified in this environment because the Docker daemon was not running.



## Issues Found

- The frontend map currently depends on a remote MapLibre demo style URL, which can cause the map to appear blank if that remote style is unavailable.
- Docker Compose runtime behavior remains unverified until Docker Desktop or the Docker daemon is running locally.
- The frontend production bundle is relatively large due to MapLibre in the main bundle.
- The ML layer is looking more complicated than I orginally thought, considering descaling the project to avoid ml use

## Engineering Conclusion

The Sprint 2 prototype is functional as a mock-first client/server feature slice. It demonstrates a working dashboard, a backend API, and the main code paths were verified through builds, tests, and targeted smoke checks. The largest remaining risks are operational rather than architectural: live browser verification with the backend enabled, Docker runtime verification, and the current external dependency on the MapLibre demo basemap.
