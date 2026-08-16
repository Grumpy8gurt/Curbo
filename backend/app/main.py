from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import Settings, get_settings
from app.db import initialize_database
from app.middleware import ProductionSafetyMiddleware
from app.routers import annotations, corridors, health, layers, reports
from app.services.eugene_data_service import EugeneDataService
from app.services.app_store import AppStore
from app.security import require_authenticated_principal


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

        session_factory, db_status = initialize_database(resolved_settings)
        if resolved_settings.database_required and session_factory is None:
            raise RuntimeError(f"Required database is unavailable: {db_status}")
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
        collections = data_service.load_all()
        if not resolved_settings.allow_sample_data:
            for layer_name, minimum in resolved_settings.required_layer_minimums.items():
                collection = collections[layer_name]
                status = collection.get("metadata", {}).get("status")
                feature_count = len(collection.get("features", []))
                if status != "cached-eugene" or feature_count < minimum:
                    raise RuntimeError(
                        f"Required {layer_name} dataset is not production-ready: "
                        f"status={status!r}, features={feature_count}, minimum={minimum}"
                    )
        application.state.store = AppStore.from_collections(
            collections,
            resolved_settings.resolved_annotation_file,
            session_factory=session_factory,
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
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Idempotency-Key", "X-Request-ID"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=1_000, compresslevel=6)
    application.add_middleware(
        ProductionSafetyMiddleware,
        max_body_bytes=resolved_settings.max_request_body_bytes,
        mutations_per_minute=resolved_settings.mutation_rate_limit_per_minute,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=resolved_settings.trusted_hosts,
    )

    # All routers are mounted under /api so the frontend proxy target is a
    # single base URL and there is no ambiguity with static asset paths.
    application.include_router(health.router, prefix="/api")
    protected = [Depends(require_authenticated_principal)]
    for router in (layers.router, annotations.router, corridors.router, reports.router):
        application.include_router(router, prefix="/api/v1", dependencies=protected)
        # Earlier clients remain compatible while callers migrate to /api/v1.
        application.include_router(
            router,
            prefix="/api",
            dependencies=protected,
            include_in_schema=False,
        )
    return application


# Module-level singleton consumed by Uvicorn:  uvicorn app.main:app
app = create_app()
