from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env files.

    pydantic-settings merges values in priority order:
      1. Environment variables (highest)
      2. ../.env  (repo root — used during local development)
      3. .env     (backend directory — used inside Docker)
      4. Field defaults (lowest)

    The Postgres fields are only relevant when DATABASE_URL is unset and the
    optional PostGIS path is being exercised; for Sprint 3 the in-memory store
    is the default runtime.
    """

    service_name: str = "curbo-backend"
    version: str = "0.1.0"
    postgres_db: str = "curbo"
    postgres_user: str = "curbo_user"
    postgres_password: str = "curbo_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    backend_port: int = 8000
    report_dir: str = "generated_reports"
    annotation_file: str = "data/annotations.json"
    # When None the SQLAlchemy layer is skipped entirely; the store uses JSON.
    database_url: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        # Ignore unknown env vars so adding VITE_* vars to the shared .env
        # does not break pydantic-settings validation.
        extra="ignore",
    )

    @property
    def project_root(self) -> Path:
        """
        Walk up from this file to find the repo root by looking for the
        data/sample sentinel directory.  This handles three layouts:
          • local dev:  Curbo/backend/app/config.py  → parents[2] = Curbo/
          • Docker:     /app/app/config.py            → parents[1] = /app/
          • test run:   varies                        → falls back to parents[2]
        """
        config_path = Path(__file__).resolve()
        candidate_roots = [config_path.parents[2], config_path.parents[1], config_path.parents[0]]

        for candidate in candidate_roots:
            if (candidate / "data" / "sample").exists():
                return candidate
        return config_path.parents[2]

    @property
    def backend_root(self) -> Path:
        """Absolute path to the backend/ directory (parent of app/)."""
        return Path(__file__).resolve().parents[1]

    @property
    def sample_data_dir(self) -> Path:
        """
        Resolves the small sample GeoJSON directory used as a fallback when the
        full Eugene cache is absent.  Checks the project root first, then two
        additional candidates so tests and Docker both resolve correctly.
        """
        project_sample_dir = self.project_root / "data" / "sample"
        if project_sample_dir.exists():
            return project_sample_dir

        fallback_candidates = [
            self.backend_root.parent / "data" / "sample",
            self.backend_root / "data" / "sample",
        ]
        for candidate in fallback_candidates:
            if candidate.exists():
                return candidate
        return project_sample_dir

    @property
    def eugene_data_dir(self) -> Path:
        """
        Resolves the cached City of Eugene GeoJSON directory.
        Falls back to backend_root/data/eugene when the project-root path is
        absent (e.g. running tests directly from backend/).
        """
        project_data_dir = self.project_root / "data" / "eugene"
        if project_data_dir.exists():
            return project_data_dir
        return self.backend_root / "data" / "eugene"

    @property
    def resolved_annotation_file(self) -> Path:
        """Return an absolute path for the annotation JSON store regardless of
        whether annotation_file was specified as absolute or relative."""
        annotation_path = Path(self.annotation_file)
        if annotation_path.is_absolute():
            return annotation_path
        return self.backend_root / annotation_path

    @property
    def resolved_report_dir(self) -> Path:
        """Return an absolute path for the generated HTML reports directory."""
        report_path = Path(self.report_dir)
        if report_path.is_absolute():
            return report_path
        return self.backend_root / report_path

    @property
    def resolved_database_url(self) -> str | None:
        return self.database_url or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached Settings singleton.  The lru_cache means .env is parsed only once
    per process, which matters because tests can start many FastAPI instances.
    Use `get_settings.cache_clear()` in tests that mutate environment variables.
    """
    return Settings()
