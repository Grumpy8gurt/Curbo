from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile

from app.config import Settings, get_settings
from app.detector import run_mock_detection
from app.image_utils import read_image_metadata
from app.schemas import DetectionResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    application = FastAPI(
        title="Curbo ML Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.get("/health")
    def health():
        return {"status": "ok", "service": resolved_settings.ml_service_name}

    @application.post("/detect", response_model=DetectionResponse)
    async def detect(
        file: UploadFile = File(...),
        image_id: str | None = Form(default=None),
        latitude: float | None = Form(default=None),
        longitude: float | None = Form(default=None),
    ):
        metadata = await read_image_metadata(file)
        detections = run_mock_detection(
            width=metadata["width"],
            height=metadata["height"],
            latitude=latitude,
            longitude=longitude,
        )

        return {
            "image_id": image_id,
            "model_version": resolved_settings.ml_model_version,
            "detections": detections,
        }

    return application


app = create_app()
