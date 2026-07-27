from __future__ import annotations

from fastapi import Request

from app.config import Settings
from app.services.app_store import AppStore


def get_store(request: Request) -> AppStore:
    """
    FastAPI dependency that retrieves the shared AppStore from application state.
    The store is populated during the lifespan startup and lives for the process
    lifetime, so every request reads the same in-memory object.
    """
    return request.app.state.store


def get_settings_from_request(request: Request) -> Settings:
    """
    FastAPI dependency that retrieves the Settings instance from application
    state.  Prefer this over calling get_settings() directly inside routers so
    that tests can inject custom settings via a test-specific app instance.
    """
    return request.app.state.settings
