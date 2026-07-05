# Curbo ML Service

This folder contains the mock-first curb-cut detection service used for MVP integration and backend handoff testing.

## Run locally

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

## Docker

```bash
docker build -t curbo-ml ./ml
docker run --rm -p 9000:9000 curbo-ml
```

## Endpoints

- `GET /health`
- `POST /detect`

`POST /detect` accepts `multipart/form-data` with a `file` field and optional `image_id`, `latitude`, `longitude`, `road_id`, and `source` values.

The response is mock data shaped like the future real ML inference result, and the backend forwards that result into frontend-facing detection features.
