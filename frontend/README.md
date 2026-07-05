# Frontend

This frontend is a mock-first React + TypeScript + Vite dashboard for Curbo. It is designed to run before the backend and ML services exist, while still matching the planned API surface in `docs/api-contract.md`.

## Run locally

1. From `/Users/rydergilman/Desktop/SSM/Curbo/frontend`, run `npm install`.
2. Start the dev server with `npm run dev`.
3. Build a production bundle with `npm run build`.

The app uses Vite's default dev port `5173`.

## What is mocked

- Roads, curb ramps, and hydrants use local mock GeoJSON mirrored from the repository sample data.
- Annotations, AI detections, corridor summaries, uploads, and report generation are mocked in `src/api/mockData.ts`.
- The API modules under `src/api/` are structured so the Backend Agent can replace mock returns with real `fetch()` integration later.

## Current scope

- MapLibre map centered on Eugene, Oregon
- Layer toggles for MVP map content
- Corridor selection and summary panel
- Annotation prototype
- Image upload and fake detection generation
- Detection review controls
- Mock report generation
