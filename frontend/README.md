# Frontend

This React + TypeScript + Vite frontend is the Eugene-focused planning dashboard for CURBO. It calls the FastAPI backend by default. Mock data is used only when explicitly enabled.

## Run locally

1. From the repository's `frontend/` directory, run `npm ci`.
2. Start the dev server with `npm run dev`.
3. Build a production bundle with `npm run build`.
4. Run component and API tests with `npm test`.

The app uses Vite's default dev port `5173`.

The backend is enabled by default:

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=http://localhost:8000
```

## Explicit demo mode

- Network failures are shown as errors and never create browser-only “saved” data.
- Set `VITE_USE_MOCK_API=true` only to force a visibly labeled local demo.
- Layer status and feature counts are shown in the layer panel.

## Current scope

- MapLibre map centered on Eugene, Oregon
- Layer toggles for the complete 13,520-segment Eugene road snapshot, bounded sidewalk-ramp, hydrant, and bike-facility extracts, and user annotations
- Searchable road selector capped at 50 rendered options
- Corridor selection and summary panel
- Reviewer annotation tools for map-placed points and drawn lines
- Persistent annotation review status controls in the selected-feature popup
- Available curb-ramp width and slope measurements with explicit units
- Backend corridor summaries and report generation with explicit error behavior

## Live API Expectations

When `VITE_USE_MOCK_API=false`, the frontend expects the canonical API:

- `GET /api/v1/annotations` to return a GeoJSON `FeatureCollection`
- `GET /api/v1/layers/roads`
- `GET /api/v1/layers/sidewalk-ramps`
- `GET /api/v1/layers/hydrants`
- `GET /api/v1/layers/bike-lanes`
- `POST /api/v1/annotations` to accept `{ annotationType, description, geometry }` with GeoJSON `Point` or `LineString` geometry
- `PATCH /api/v1/annotations/{annotation_id}` to accept `{ status, expectedVersion }`
- `POST /api/v1/corridors/analyze` to accept `{ roadId }`
- `POST /api/v1/reports/corridor` to accept `{ roadId, format }` or `{ corridor_id, format }`
