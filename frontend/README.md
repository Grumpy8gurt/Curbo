# Frontend

This React + TypeScript + Vite frontend is the Eugene-focused planning dashboard for CURBO. It calls the FastAPI backend by default and uses compact local fallback data when the API is unavailable.

## Run locally

1. From the repository's `frontend/` directory, run `npm install`.
2. Start the dev server with `npm run dev`.
3. Build a production bundle with `npm run build`.

The app uses Vite's default dev port `5173`.

The backend is enabled by default:

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=http://localhost:8000
```

## Offline fallback

- API modules catch network failures and return compact data from `src/api/fallbackData.ts`.
- Set `VITE_USE_MOCK_API=true` to force fallback mode.
- Layer status and feature counts are shown in the layer panel.

## Current scope

- MapLibre map centered on Eugene, Oregon
- Layer toggles for Eugene roads, sidewalk ramps, hydrants, bike facilities, and annotations
- Corridor selection and summary panel
- Annotation prototype
- Backend corridor summaries and report generation with fallback behavior

## Live API Expectations

When `VITE_USE_MOCK_API=false`, the frontend expects:

- `GET /api/annotations` to return a GeoJSON `FeatureCollection`
- `GET /api/layers/roads`
- `GET /api/layers/sidewalk-ramps`
- `GET /api/layers/hydrants`
- `GET /api/layers/bike-lanes`
- `POST /api/annotations` to accept `{ annotationType, description, latitude, longitude }`
- `POST /api/corridors/analyze` to accept `{ roadId }`
- `POST /api/reports/corridor` to accept `{ roadId, format }` or `{ corridor_id, format }`
