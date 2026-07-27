from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import annotation, corridor_report, curb_ramp, hydrant, road
from app.models.base import Base


def build_engine(settings: Settings):
    """
    Create a SQLAlchemy engine from the resolved DATABASE_URL.
    SQLite requires check_same_thread=False because FastAPI can serve requests
    from multiple threads while sharing one engine; PostgreSQL does not need it.
    """
    database_url = settings.resolved_database_url
    if database_url is None:
        raise ValueError("DATABASE_URL is not configured")
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, future=True, connect_args=connect_args)


def initialize_database(settings: Settings) -> tuple[sessionmaker[Session] | None, str]:
    """
    Attempt to connect to the configured database and run DDL migrations.

    Returns a (session_factory, status_string) tuple so the caller can log
    the outcome and still start the server when the DB is unavailable.

    Status values:
      "disabled"                   — DATABASE_URL not set; JSON store is active
      "connected"                  — engine and tables initialised successfully
      "database-unavailable (...)" — connection or DDL failed; store is still JSON
    """
    if settings.resolved_database_url is None:
        return None, "disabled"
    try:
        engine = build_engine(settings)
        # create_all is idempotent: safe to call on every startup.
        Base.metadata.create_all(engine)
        return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True), "connected"
    except Exception as exc:  # pragma: no cover - exercised only when DB is unavailable
        return None, f"database-unavailable ({exc.__class__.__name__})"
