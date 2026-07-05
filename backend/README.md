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
- `POST /api/detection/curb-cuts`
- `PATCH /api/detection/{detection_id}`
- `POST /api/reports/corridor`
- `GET /api/reports/{report_id}/download`

## Mock Behavior

- Roads, curb ramps, and hydrants are loaded from the sample GeoJSON under `../data/sample`.
- Annotations, detections, uploaded image metadata, and generated reports are stored in memory for MVP development.
- Uploaded files are written to the local `uploads/` directory.
- Detection results come from a mock detection service that is shaped to later call an ML service at `http://localhost:9000/detect`.
- Corridor analysis uses lightweight spatial heuristics and bbox checks instead of real PostGIS buffering.

## Database Status

- SQLAlchemy models are included for `roads`, `curb_ramps`, `hydrants`, `annotations`, `detections`, `uploaded_images`, and `corridor_reports`.
- On startup the app attempts to create tables using the configured database URL.
- If PostgreSQL/PostGIS is unavailable, the API still starts and serves mock/sample-backed responses so the frontend is not blocked.

## Frontend Integration Notes

- Layer endpoints return GeoJSON `FeatureCollection` payloads.
- `GET /api/annotations` returns annotation records, while `GET /api/layers/annotations` returns those same records as a map layer.
- The frontend functions `getRoads()`, `getCurbRamps()`, `getHydrants()`, `getAnnotations()`, `createAnnotation(annotation)`, `analyzeCorridor(roadId)`, `uploadImage(file)`, `runCurbCutDetection(imageId)`, and `generateCorridorReport(roadId)` map directly to the implemented endpoints.
- CORS is enabled for `http://localhost:5173` and common local development origins.

## ML Integration Notes

The ML agent does not need to change the API shape right away. The cleanest upgrade path is to replace the mock logic inside `app/services/detection_service.py` with a real request to the ML service while keeping the existing request and response schema stable.

## Tests

Run the backend tests with:

```bash
cd backend
pytest
```
