# CURBO Backend

This FastAPI service normalizes CURBO's cached City of Eugene GIS layers, persists planner annotations and report metadata transactionally when a database is configured, calculates corridor summaries, and generates HTML reports.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL as the production annotation/report database
- Cached Eugene GeoJSON with compact sample fallback data
- Alembic migrations, optimistic concurrency, idempotent creates, and a locked JSON local-development fallback

## Run Locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Environment Variables

The backend reads configuration from the repository-root `.env` file and process environment. The current prototype does not require a database.

```env
POSTGRES_DB=curbo
POSTGRES_USER=curbo_user
POSTGRES_PASSWORD=replace-with-a-long-random-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
BACKEND_PORT=8000
REPORT_DIR=generated_reports
ANNOTATION_FILE=data/annotations.json
```

- `DATABASE_URL`: enables transactional SQLAlchemy persistence. Production requires it.
- `ENVIRONMENT=production`: enables fail-closed production validation.
- `AUTH_REQUIRED=true` and `API_KEY`: protect all data routes. Production requires a key of at least 32 characters.
- `CORS_ORIGINS` and `TRUSTED_HOSTS`: must name the exact HTTPS production host.
- `DATABASE_REQUIRED=true`: prevents startup without the configured database.

## API Endpoints

Data routes are registered under `/api/v1`. The former `/api` forms remain temporary compatibility aliases. Health probes remain under `/api`.

- `GET /api/health`
- `GET /api/live`
- `GET /api/ready`
- `GET /api/v1/layers/roads`
- `GET /api/v1/layers/sidewalk-ramps`
- `GET /api/v1/layers/curb-ramps`
- `GET /api/v1/layers/hydrants`
- `GET /api/v1/layers/bike-lanes`
- `GET /api/v1/layers/annotations`
- `GET /api/v1/annotations`
- `POST /api/v1/annotations`
- `PATCH /api/v1/annotations/{annotation_id}`
- `POST /api/v1/corridors/analyze`
- `POST /api/v1/reports/corridor`
- `GET /api/v1/reports/{report_id}/download`

## Data and Fallback Behavior

- Eugene layers load from `../data/eugene` and are normalized by `EugeneDataService`.
- Sidewalk-ramp normalization preserves published width, grade, and cross-slope measurements.
- Missing cached layers can fall back to `../data/sample` in local development. Production rejects sample/incomplete data when configured as required.
- With `DATABASE_URL`, annotations and report metadata use database transactions. Without it, local development can use `ANNOTATION_FILE`.
- Corridor analysis uses a bounding-box prefilter followed by metric point/segment and segment/segment distance checks. It remains an in-memory linear scan rather than a PostGIS query.

## Database and migrations

- Development/test databases bootstrap automatically. Production never creates tables during web-server startup.
- Apply `DATABASE_URL=... .venv/bin/alembic upgrade head` before production startup.
- Production startup verifies the expected migration revision and fails if the database is absent or stale.
- See `docs/operations-runbook.md` for deployment, backup, restore, monitoring, and rollback requirements.

## Frontend Integration Notes

- Layer endpoints return GeoJSON `FeatureCollection` payloads.
- `GET /api/v1/annotations` returns a GeoJSON `FeatureCollection` because the frontend stores annotations as map features.
- `POST /api/v1/annotations` accepts `{ annotationType, description, geometry }`, where geometry is a GeoJSON `Point` or `LineString`. Latitude/longitude remain a point-only compatibility input.
- Explicit Point and LineString positions are validated for finite, in-range longitude and latitude.
- `PATCH /api/v1/annotations/{annotation_id}` requires `{ status, expectedVersion }`; stale updates return HTTP 409.
- Reviewer annotations are notes only and do not become authoritative curb-ramp, hydrant, or bike-lane inventory features.
- `POST /api/v1/corridors/analyze` accepts `{ roadId }` and returns the current `CorridorSummary` shape used by the React app.
- `POST /api/v1/reports/corridor` accepts `{ corridor_id, format }` or `{ roadId, format }` and returns the current `CorridorReportResult` shape.
- Local CORS supports the Vite development origin. Production accepts only configured HTTPS origins.

## Tests

Run the backend tests with:

```bash
cd backend
.venv/bin/python -m pytest -q
```
