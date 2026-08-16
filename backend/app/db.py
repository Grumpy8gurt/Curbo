from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.models import annotation, corridor_report, curb_ramp, hydrant, road
from app.models.base import Base

EXPECTED_DATABASE_REVISION = "20260815_0001"


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
    engine_options: dict[str, object] = {"future": True, "connect_args": connect_args}
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        engine_options["poolclass"] = StaticPool
    return create_engine(database_url, **engine_options)


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
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        # Tests and local development can bootstrap an empty database. Production
        # schema changes must be applied explicitly with Alembic before startup.
        if settings.environment != "production":
            Base.metadata.create_all(engine)
        else:
            inspector = inspect(engine)
            required_tables = {"annotations", "corridor_reports", "alembic_version"}
            missing_tables = required_tables.difference(inspector.get_table_names())
            if missing_tables:
                raise RuntimeError(
                    "database migrations are missing: " + ", ".join(sorted(missing_tables))
                )
            with engine.connect() as connection:
                revision = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one_or_none()
            if revision != EXPECTED_DATABASE_REVISION:
                raise RuntimeError(
                    f"database revision is {revision!r}; expected {EXPECTED_DATABASE_REVISION!r}"
                )
        return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True), "connected"
    except Exception as exc:  # pragma: no cover - exercised only when DB is unavailable
        return None, f"database-unavailable ({exc.__class__.__name__})"
