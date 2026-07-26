# Curbo Backend

This backend provides the MVP API for Curbo, the sidewalk surveying and management dashboard. It serves map-ready GeoJSON layers, accepts planner annotations, and generates lightweight corridor reports for frontend integration.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL + PostGIS as the intended long-term database
- Mock GeoJSON and in-memory storage for local development fallback

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

The backend reads configuration from environment variables and builds the database URL automatically.

```env
POSTGRES_DB=ssm
POSTGRES_USER=ssm_user
POSTGRES_PASSWORD=ssm_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
BACKEND_PORT=8000
REPORT_DIR=generated_reports
```

Optional:

- `DATABASE_URL`: overrides the generated PostgreSQL URL when you want SQLite or a custom DSN.

## API Endpoints

All routes are registered under `/api`.

- `GET /api/health`
- `GET /api/layers/roads`
- `GET /api/layers/curb-ramps`
- `GET /api/layers/hydrants`
- `GET /api/layers/annotations`
- `GET /api/annotations`
- `POST /api/annotations`
- `PATCH /api/annotations/{annotation_id}`
- `POST /api/corridors/analyze`
- `POST /api/reports/corridor`
- `GET /api/reports/{report_id}/download`

## Mock Behavior

- Roads, curb ramps, and hydrants are loaded from the sample GeoJSON under `../data/sample`.
- Annotations and generated reports are stored in memory for MVP development.
- Corridor analysis uses lightweight spatial heuristics and bbox checks instead of real PostGIS buffering.

## Database Status

- SQLAlchemy models are included for `roads`, `curb_ramps`, `hydrants`, `annotations`, and `corridor_reports`.
- On startup the app attempts to create tables using the configured database URL.
- If PostgreSQL/PostGIS is unavailable, the API still starts and serves mock/sample-backed responses so the frontend is not blocked.

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
