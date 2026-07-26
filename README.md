# CURBO

**Sidewalk Surveying and Management Dashboard**

CURBO is a geospatial planning dashboard for reviewing street, pedestrian, bicycle, and civic infrastructure around Eugene, Oregon.

## Sprint 3 Expansion

Sprint 3 integrates a local cache of City of Eugene GIS infrastructure data, adds offline-safe data refresh and validation scripts, serves normalized layers through FastAPI, and uses lightweight JSON persistence for user annotations. The previous ML workflow was removed from Sprint 3 scope so the prototype can focus on maintainable civic-data integration.

## Current Behavior

- Displays cached Eugene roads, sidewalk ramps, fire hydrants, and bike facilities.
- Uses stable backend layer endpoints with `/api/layers/curb-ramps` retained as an alias.
- Falls back to small frontend samples if the backend is unavailable.
- Persists backend annotations in `backend/data/annotations.json`.
- Calculates a simple corridor summary from nearby Eugene layers and user annotations.

## Run Locally

Copy `.env.example` to `.env`. PostGIS is optional scaffolding and can be started with its Compose profile:

```bash
docker compose --profile database up -d postgres
```

The Sprint 3 runtime does not require PostGIS. Set `DATABASE_URL` only when explicitly testing the future database path.

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
```

The fetch script uses documented public City endpoints, allows `EUGENE_*_URL` overrides, and preserves existing cache files when the network fails. Set `EUGENE_CACHE_ONLY=true` to skip network requests. It uses only Python's standard library and requires no API key.

## Tests

```bash
cd backend && pytest
cd frontend && npm run build
python scripts/validate_geojson.py
docker compose config
```

## Architecture and Dependencies

- `frontend/`: React, TypeScript, Vite, and MapLibre.
- `backend/`: FastAPI, Pydantic, and SQLAlchemy.
- `data/eugene/`: cached civic infrastructure GeoJSON.
- `data/sample/`: compact offline fallback GeoJSON retained from earlier sprints.
- `scripts/`: safe fetch and validation utilities.
- `postgres`: PostGIS-ready service retained for future persistence work.

## Intentionally Not Included

- ML inference, image upload, or detection-review UI.
- Production authentication and authorization.
- Full PostGIS ingestion or production-grade spatial analysis.
- Live external GIS requests during normal app startup.
- PDF report rendering.

## Sprint 3 Submission Summary

- GitHub repository URL: https://github.com/Grumpy8gurt/Curbo
- Sprint 3 branch name: `sprint-3-prototype`
- Sprint 3 expansion: CURBO integrates City of Eugene GIS-style infrastructure data and removes the ML layer to focus on a cleaner geospatial planning dashboard.
- Demo sentence: Run the backend and frontend, open the CURBO dashboard, toggle Eugene infrastructure layers, add an annotation, and view a corridor summary.
