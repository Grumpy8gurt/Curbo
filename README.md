# CURBO

**Sidewalk Surveying and Management Dashboard**

CURBO is a geospatial planning dashboard for reviewing street, pedestrian, bicycle, and civic infrastructure around Eugene, Oregon.

## Sprint 4 Capability

Sprint 4 completes the annotation review workflow. A user can create a point or
line note, select it on the map, and move it through `pending`, `reviewed`,
`confirmed`, or `rejected`; each change is persisted by the backend. Curb-ramp
inspection preserves and displays published aggregate and left/right width,
grade, and cross-slope measurements when the Eugene source provides them.
Corridor review is status-aware: rejected notes remain in history without
inflating active concerns, while human-readable signals explain a limited
Low/Medium/High review-attention prompt. Explicit GeoJSON input is range-checked
before it can enter the annotation store.

## Sprint 3 Expansion

Sprint 3 integrates a local cache of City of Eugene GIS infrastructure data, adds offline-safe data refresh and validation scripts, serves normalized layers through FastAPI, and uses lightweight JSON persistence for user annotations. The previous ML workflow was removed from Sprint 3 scope so the prototype can focus on maintainable civic-data integration.

## Current Behavior

- Displays the complete cached Eugene street-line snapshot with road-name labels, plus sidewalk ramps, fire hydrants, and bike facilities.
- Uses stable backend layer endpoints with `/api/layers/curb-ramps` retained as an alias.
- Falls back to small frontend samples if the backend is unavailable.
- Persists backend annotations in `backend/data/annotations.json`.
- Supports reviewer-created point and line annotations on the map.
- Supports persistent annotation status review from the selected-feature popup.
- Displays available curb-ramp dimensions with units and screening-only
  field-review prompts based on published dimensional references.
- Calculates status-aware missing-curb-cut, bike-gap, intersection-safety,
  parking/loading, and needs-review counts from nearby annotations.
- Explains review attention and missing decision inputs without producing a
  safety, project-priority, or accessibility-compliance score.
- Refreshes the selected corridor and invalidates old report links after
  annotation creation or status review.
- Generates readable HTML evidence with labeled metrics, signals, notes, and
  data limitations.

## Run Locally

Copy `.env.example` to `.env`. PostGIS is optional scaffolding and can be started with its Compose profile:

```bash
docker compose --profile database up -d postgres
```

The current prototype does not require PostGIS. Set `DATABASE_URL` only when explicitly testing the future database path.
In Docker Compose, annotations persist in the `annotation-data` volume at `/app/data/runtime/annotations.json`.

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend calls `http://localhost:8000` by default. Set `VITE_USE_MOCK_API=true` only when intentionally testing the local fallback.

## Eugene Data Tools

The committed cache in `data/eugene/` keeps the demo runnable without network access.

```bash
python scripts/validate_geojson.py
python scripts/fetch_eugene_data.py
python scripts/fetch_eugene_data.py --layer roads
```

The road cache contains the complete 13,520-feature service snapshot captured on July 27, 2026. The fetch script uses documented public City endpoints, supports selective `--layer` refreshes and `EUGENE_*_URL` overrides, and preserves existing cache files when the network fails. Set `EUGENE_CACHE_ONLY=true` to skip network requests. It uses only Python's standard library and requires no API key.

## Tests

```bash
(cd backend && python3 -m pytest -q)
(cd frontend && npm test)
(cd frontend && npm run build)
(cd frontend && npm audit)
python3 scripts/validate_geojson.py
docker compose config
./scripts/verify_sprint4.sh
```

## Architecture and Dependencies

- `frontend/`: React, TypeScript, Vite, and MapLibre.
- `backend/`: FastAPI, Pydantic, and SQLAlchemy.
- `data/eugene/`: cached civic infrastructure GeoJSON.
- `data/sample/`: compact offline fallback GeoJSON retained from earlier sprints.
- `scripts/`: safe fetch and validation utilities.
- `postgres`: PostGIS-ready service retained for future persistence work.

Sprint 4 includes 27 backend tests and 9 frontend tests in 6 files. Coverage
includes geometry validation, restart persistence, rejected-vs-confirmed
corridor effects, the synchronized API/fallback contract, report readability,
curb-ramp sentinel handling, dimensional prompts, and review UI behavior.

## Intentionally Not Included

- ML inference, image upload, or detection-review UI.
- Production authentication and authorization.
- Full PostGIS ingestion or production-grade spatial analysis.
- Live external GIS requests during normal app startup.
- PDF report rendering.
- Live crash/speed/volume ingestion, routing, project ranking, or a compliance
  determination.

## Sprint 4 Submission Summary

- GitHub repository URL: https://github.com/Grumpy8gurt/Curbo
- Sprint 4 branch: `agent/curbo-planner-quality`
- Completed capability: status-aware annotation review persists reviewer
  decisions and reflects active concerns in corridor analysis and reports.
- Quality improvement: backend schema, frontend types, offline fallbacks,
  readable HTML output, focused tests, limitations, and responsive review UI
  agree on explainable user effects.

## Sprint 3 Submission Summary

- GitHub repository URL: https://github.com/Grumpy8gurt/Curbo
- Sprint 3 branch name: `sprint-3-prototype`
- Sprint 3 expansion: CURBO integrates City of Eugene GIS-style infrastructure data and removes the ML layer to focus on a cleaner geospatial planning dashboard.
- Demo sentence: Run the backend and frontend, open the CURBO dashboard, inspect the complete labeled Eugene road layer, add an annotation, and view a corridor summary.
