# Curbo

**Serious name:** Sidewalk Surveying and Management Dashboard

Curbo is a geospatial planning dashboard for city planners, civil engineers, transportation planners, and surveyors. It visualizes roads, curb ramps, hydrants, planner annotations, corridor summaries, uploaded street images, and mock AI curb-cut detections.

## What The App Does

- `frontend/`: React + TypeScript dashboard with a MapLibre planning UI
- `backend/`: FastAPI API serving GeoJSON layers, annotations, uploads, detections, and corridor reports
- `ml/`: FastAPI mock detection service with a stable `/detect` interface for future model integration
- `postgres`: PostGIS-ready local database for the long-term architecture

## Local Development

1. Copy `.env.example` to `.env`.
2. Start Postgres:

```bash
docker compose up -d postgres
```

3. Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

4. Start the ML service:

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

5. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

6. To exercise the live backend from the frontend, set `VITE_USE_MOCK_API=false` in the frontend environment.

## What Is Mocked

- Backend map layers load from `data/sample/*.geojson`
- Backend annotations, uploads, detections, and report metadata are stored in memory for MVP integration work
- ML detections are mocked but returned in a stable response shape
- Frontend runs in local mock mode by default via `VITE_USE_MOCK_API=true`
- Set `VITE_USE_MOCK_API=false` to exercise the live backend API that now matches the frontend fetch contract

## What Remains Future Work

- Real PostGIS-backed persistence and spatial analysis
- Replacing mock ML detections with model inference
- Richer report export and report assets
- More complete infrastructure layers such as parcels, bike lanes, and bus stops
- Full end-to-end Dockerized frontend workflow

## Repository Layout

- `docs/`: architecture, API contract, data model, and agent notes
- `frontend/`: Vite + React planning dashboard
- `backend/`: FastAPI MVP API
- `ml/`: FastAPI mock ML service
- `data/`: sample GeoJSON and future import data
- `scripts/`: local setup helpers
- `tests/`: integration reports and future shared validation
