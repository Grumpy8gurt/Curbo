# CURBO Backend

This FastAPI service normalizes CURBO's cached City of Eugene GIS layers, persists planner annotations to JSON, calculates lightweight corridor summaries, and generates HTML reports.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL + PostGIS as the intended long-term database
- Cached Eugene GeoJSON with compact sample fallback data
- Atomic JSON-file annotation persistence

## Run Locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Environment Variables

The backend reads configuration from the repository-root `.env` file and process environment. The Sprint 3 runtime does not require a database.

```env
POSTGRES_DB=curbo
POSTGRES_USER=curbo_user
POSTGRES_PASSWORD=curbo_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
BACKEND_PORT=8000
REPORT_DIR=generated_reports
ANNOTATION_FILE=data/annotations.json
```

Optional:

- `DATABASE_URL`: enables optional SQLAlchemy/PostGIS scaffolding with a PostgreSQL, SQLite, or other supported DSN. It is disabled by default.

## API Endpoints

All routes are registered under `/api`.

- `GET /api/health`
- `GET /api/layers/roads`
- `GET /api/layers/sidewalk-ramps`
- `GET /api/layers/curb-ramps`
- `GET /api/layers/hydrants`
- `GET /api/layers/bike-lanes`
- `GET /api/layers/annotations`
- `GET /api/annotations`
- `POST /api/annotations`
- `PATCH /api/annotations/{annotation_id}`
- `POST /api/corridors/analyze`
- `POST /api/reports/corridor`
- `GET /api/reports/{report_id}/download`

## Data and Fallback Behavior

- Eugene layers load from `../data/eugene` and are normalized by `EugeneDataService`.
- Missing cached layers fall back to `../data/sample` where a matching sample exists.
- Annotations persist to `ANNOTATION_FILE`; reports are written under `REPORT_DIR`.
- Corridor analysis uses lightweight bounding-box checks instead of PostGIS buffering.

## Database Status

- SQLAlchemy models are included for `roads`, `curb_ramps`, `hydrants`, `annotations`, and `corridor_reports`.
- On startup the app attempts to create tables using the configured database URL.
- If PostgreSQL/PostGIS is unavailable, the API still starts and serves cached GeoJSON because layer loading and annotation persistence are independent.

## Frontend Integration Notes

- Layer endpoints return GeoJSON `FeatureCollection` payloads.
- `GET /api/annotations` returns a GeoJSON `FeatureCollection` because the frontend stores annotations as map features.
- `POST /api/annotations` accepts the frontend draft shape `{ annotationType, description, latitude, longitude }`.
- `POST /api/corridors/analyze` accepts `{ roadId }` and returns the current `CorridorSummary` shape used by the React app.
- `POST /api/reports/corridor` accepts `{ corridor_id, format }` or `{ roadId, format }` and returns the current `CorridorReportResult` shape.
- CORS is enabled for `http://localhost:5173` and common local development origins.

## Tests

Run the backend tests with:

```bash
cd backend
pytest
```
