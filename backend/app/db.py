from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import annotation, corridor_report, curb_ramp, detection, hydrant, road, uploaded_image
from app.models.base import Base


def build_engine(settings: Settings):
    connect_args: dict[str, object] = {}
    if settings.resolved_database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.resolved_database_url, future=True, connect_args=connect_args)


def initialize_database(settings: Settings) -> tuple[sessionmaker[Session] | None, str]:
    try:
        engine = build_engine(settings)
        Base.metadata.create_all(engine)
        return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True), "connected"
    except Exception as exc:  # pragma: no cover - exercised only when DB is unavailable
        return None, f"mock-fallback ({exc.__class__.__name__})"
