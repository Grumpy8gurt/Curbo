# Sprint 2 Manual Verification

## Actions Performed

1. Reviewed the repository structure, sample GeoJSON, and Sprint 2 documentation files.
2. Built the frontend with `cd frontend && npm run build`.
3. Ran backend tests with `cd backend && pytest`.
4. Ran ML tests with `cd ml && pytest`.
5. Started the backend locally with `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
6. Started the ML service locally with `uvicorn app.main:app --host 127.0.0.1 --port 9000`.
7. Performed targeted backend smoke checks for:
   - `GET /api/health`
   - `GET /api/layers/roads`
   - `POST /api/annotations`
   - `POST /api/uploads/images`
   - `POST /api/detection/curb-cuts`
   - `PATCH /api/detection/{detection_id}`
   - `POST /api/reports/corridor`
   - `GET /api/reports/{report_id}/download`
8. Loaded the frontend locally and confirmed that the MapLibre canvas rendered after replacing the remote demo basemap dependency with a local style.
9. Validated Docker Compose syntax with `docker compose config`.
10. Investigated the previous Docker startup failure and traced it to the backend container missing the sample data directory needed at startup.

## Expected Results

- The frontend should build without TypeScript errors.
- The backend should start, pass tests, and expose the main MVP routes.
- The ML service should start, pass tests, and return a stable mock detection payload.
- The frontend should render a working map view instead of a blank panel.
- Docker Compose should parse successfully, and the backend container should have access to the sample GeoJSON files it needs at startup.

## Observed Results

- Frontend build succeeded.
- Backend tests succeeded.
- ML tests succeeded.
- Local backend startup succeeded.
- Local ML startup succeeded.
- Backend smoke checks returned successful responses for the tested MVP routes.
- The frontend rendered a live MapLibre canvas locally after the basemap fix.
- Docker Compose configuration parsed successfully.
- The earlier Docker backend crash was consistent with the backend image not including `data/sample`; the compose and Dockerfile configuration were updated to address that path issue.

## Issues Found

- The application is still mock-first. Roads, curb ramps, hydrants, annotations, detections, and reports are not yet fully persisted through a production-style database workflow.
- Docker runtime behavior still needs one more full end-to-end verification on a machine with Docker Desktop or a running Docker daemon after the backend image fix.
- The frontend production bundle is still fairly large because MapLibre is included in the main bundle.
- The ML layer is intentionally shallow for Sprint 2 and may be reduced further if keeping it would distract from the core planning workflow.

## Engineering Conclusion

The Sprint 2 prototype now demonstrates a complete, explainable feature slice: the frontend can load map data, a user can interact with the map, the backend can return GeoJSON and corridor analysis, uploads can flow into the mock detection path, and reports can be generated and downloaded. The biggest remaining work is not basic wiring anymore; it is scope control, persistent data, and one more end-to-end Docker verification after the image-path fix.
