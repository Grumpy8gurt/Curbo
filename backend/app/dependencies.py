from __future__ import annotations

from fastapi import Request

from app.config import Settings
from app.services.app_store import AppStore


def get_store(request: Request) -> AppStore:
    return request.app.state.store


def get_settings_from_request(request: Request) -> Settings:
    return request.app.state.settings
