# Frontend

This frontend is a mock-first React + TypeScript + Vite dashboard for Curbo. It is designed to run before the backend and ML services exist, while still matching the planned API surface in `docs/api-contract.md`.

## Run locally

1. From `/Users/rydergilman/Desktop/SSM/Curbo/frontend`, run `npm install`.
2. Start the dev server with `npm run dev`.
3. Build a production bundle with `npm run build`.

The app uses Vite's default dev port `5173`.

To point the app at the backend instead of local mocks, set:

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=http://localhost:8000
```

## What is mocked

- Roads, curb ramps, and hydrants use local mock GeoJSON mirrored from the repository sample data by default.
- Annotations, AI detections, corridor summaries, uploads, and report generation are mocked in `src/api/mockData.ts`.
- The API modules under `src/api/` now also include response adapters so `VITE_USE_MOCK_API=false` can talk to the current backend routes.

## Current scope

- MapLibre map centered on Eugene, Oregon
- Layer toggles for MVP map content
- Corridor selection and summary panel
- Annotation prototype
- Image upload and fake detection generation
- Detection review controls
- Mock report generation

## Live API Expectations

When `VITE_USE_MOCK_API=false`, the frontend expects:

- `GET /api/annotations` to return a GeoJSON `FeatureCollection`
- `POST /api/annotations` to accept `{ annotationType, description, latitude, longitude }`
- `POST /api/corridors/analyze` to accept `{ roadId }`
- `POST /api/uploads/images` to accept multipart field `image`
- `GET /api/detection/curb-cuts` to return a detection `FeatureCollection`
- `POST /api/detection/curb-cuts` to accept `{ upload_id }` or `{ image_id }` and return one detection `Feature`
- `PATCH /api/detection/{detectionId}` or `PATCH /api/detections/{detectionId}` to update review state
- `POST /api/reports/corridor` to accept `{ roadId, format }` or `{ corridor_id, format }`
