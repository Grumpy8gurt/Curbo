from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.db import initialize_database
from app.routers import annotations, corridors, detection, health, layers, reports, uploads
from app.services.mock_data import AppStore


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        resolved_settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)
        resolved_settings.resolved_report_dir.mkdir(parents=True, exist_ok=True)
        session_factory, db_status = initialize_database(resolved_settings)
        application.state.settings = resolved_settings
        application.state.db_session_factory = session_factory
        application.state.db_status = db_status
        application.state.store = AppStore.from_sample_dir(resolved_settings.sample_data_dir)
        yield

    application = FastAPI(
        title="Curbo Backend API",
        version=resolved_settings.version,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router, prefix="/api")
    application.include_router(layers.router, prefix="/api")
    application.include_router(annotations.router, prefix="/api")
    application.include_router(corridors.router, prefix="/api")
    application.include_router(uploads.router, prefix="/api")
    application.include_router(detection.router, prefix="/api")
    application.include_router(reports.router, prefix="/api")
    return application


app = create_app()
