from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.db import initialize_database
from app.routers import annotations, corridors, health, layers, reports
from app.services.eugene_data_service import EugeneDataService
from app.services.app_store import AppStore


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    App factory — accepts an optional Settings override so tests can inject
    custom paths (e.g. a tmp annotation file) without touching process env vars.
    The module-level `app` instance uses the default cached Settings singleton.
    """
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """
        FastAPI lifespan runs once on startup (before `yield`) and once on
        shutdown (after `yield`).  All startup work lives here so the app state
        is fully initialised before the first request is served.
        """
        # Ensure the report output directory exists before any router needs it.
        resolved_settings.resolved_report_dir.mkdir(parents=True, exist_ok=True)

        # DB initialisation is a no-op when DATABASE_URL is unset; the store
        # always works regardless of the returned session_factory being None.
        session_factory, db_status = initialize_database(resolved_settings)
        application.state.settings = resolved_settings
        application.state.db_session_factory = session_factory
        application.state.db_status = db_status

        # Load the City of Eugene GeoJSON cache into memory at startup.
        # EugeneDataService falls back to data/sample/ when the full cache is
        # missing, so the API remains functional in offline / CI environments.
        data_service = EugeneDataService(
            resolved_settings.eugene_data_dir,
            resolved_settings.sample_data_dir,
        )
        application.state.store = AppStore.from_collections(
            data_service.load_all(),
            resolved_settings.resolved_annotation_file,
        )
        yield
        # No explicit teardown needed; the store is in-memory and annotations
        # are flushed to disk on every write, not on shutdown.

    application = FastAPI(
        title="CURBO Backend API",
        version=resolved_settings.version,
        lifespan=lifespan,
    )

    # Allow the Vite dev server (5173) and common alternative ports.
    # cors_origins is configurable via .env for production deployments.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # All routers are mounted under /api so the frontend proxy target is a
    # single base URL and there is no ambiguity with static asset paths.
    application.include_router(health.router, prefix="/api")
    application.include_router(layers.router, prefix="/api")
    application.include_router(annotations.router, prefix="/api")
    application.include_router(corridors.router, prefix="/api")
    application.include_router(reports.router, prefix="/api")
    return application


# Module-level singleton consumed by Uvicorn:  uvicorn app.main:app
app = create_app()
