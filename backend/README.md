# Curbo Backend

This backend provides the MVP API for Curbo, the sidewalk surveying and management dashboard. It serves map-ready GeoJSON layers, accepts planner annotations and image uploads, runs mock curb-cut detections, and generates lightweight corridor reports for frontend integration.

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
UPLOAD_DIR=uploads
REPORT_DIR=generated_reports
ML_SERVICE_URL=http://localhost:9000/detect
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
- `GET /api/layers/detections`
- `GET /api/annotations`
- `POST /api/annotations`
- `PATCH /api/annotations/{annotation_id}`
- `POST /api/corridors/analyze`
- `POST /api/uploads/images`
- `GET /api/detection/curb-cuts`
- `POST /api/detection/curb-cuts`
- `PATCH /api/detections/{detection_id}`
- `POST /api/reports/corridor`
- `GET /api/reports/{report_id}/download`

## Mock Behavior

- Roads, curb ramps, and hydrants are loaded from the sample GeoJSON under `../data/sample`.
- Annotations, detections, uploaded image metadata, and generated reports are stored in memory for MVP development.
- Uploaded files are written to the local `uploads/` directory.
- Detection requests are forwarded to the ML service at `ML_SERVICE_URL` when it is available, with a backend fallback if the ML service is offline during local development.
- Corridor analysis uses lightweight spatial heuristics and bbox checks instead of real PostGIS buffering.

## Database Status

- SQLAlchemy models are included for `roads`, `curb_ramps`, `hydrants`, `annotations`, `detections`, `uploaded_images`, and `corridor_reports`.
- On startup the app attempts to create tables using the configured database URL.
- If PostgreSQL/PostGIS is unavailable, the API still starts and serves mock/sample-backed responses so the frontend is not blocked.

## Frontend Integration Notes

- Layer endpoints return GeoJSON `FeatureCollection` payloads.
- `GET /api/annotations` returns a GeoJSON `FeatureCollection` because the frontend stores annotations as map features.
- `POST /api/annotations` accepts the frontend draft shape `{ annotationType, description, latitude, longitude }`.
- `POST /api/corridors/analyze` accepts `{ roadId }` and returns the current `CorridorSummary` shape used by the React app.
- `POST /api/uploads/images` accepts multipart field `image` and returns `{ uploadId, filename, status }`.
- `GET /api/detection/curb-cuts` returns the detection layer as a GeoJSON `FeatureCollection`.
- `POST /api/detection/curb-cuts` accepts `{ upload_id }` and returns a single detection `Feature`.
- `POST /api/reports/corridor` accepts `{ corridor_id, format }` and returns the current `CorridorReportResult` shape.
- CORS is enabled for `http://localhost:5173` and common local development origins.

## ML Integration Notes

The backend now calls the ML service through `app/services/detection_service.py` using multipart upload to `/detect`. If the ML service is down, the backend falls back to a local mock detection so the frontend remains usable.

## Tests

Run the backend tests with:

```bash
cd backend
pytest
```
