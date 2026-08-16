from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env files.

    pydantic-settings merges values in priority order:
      1. Environment variables (highest)
      2. ../.env  (repo root — used during local development)
      3. .env     (backend directory — used inside Docker)
      4. Field defaults (lowest)

    PostgreSQL is required in production and optional during local development.
    Without DATABASE_URL, annotations use the locked JSON development store.
    """

    service_name: str = "curbo-backend"
    version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
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
    database_required: bool = False
    auth_required: bool = False
    api_key: SecretStr | None = None
    max_request_body_bytes: int = Field(default=1_000_000, ge=16_384, le=10_000_000)
    mutation_rate_limit_per_minute: int = Field(default=60, ge=1, le=10_000)
    report_retention_days: int = Field(default=30, ge=1, le=3650)
    max_report_files: int = Field(default=1_000, ge=1, le=100_000)
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    allow_sample_data: bool = True
    required_layer_minimums: dict[str, int] = Field(
        default_factory=lambda: {
            "roads": 10_000,
            "curb_ramps": 1_000,
            "hydrants": 1_000,
            "bike_lanes": 100,
        }
    )
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

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        """Refuse production startup when mandatory security controls are absent."""
        if self.environment != "production":
            return self

        if not self.auth_required:
            raise ValueError("AUTH_REQUIRED must be true in production")
        if self.api_key is None or len(self.api_key.get_secret_value()) < 32:
            raise ValueError("API_KEY must contain at least 32 characters in production")
        if not self.database_required or self.resolved_database_url is None:
            raise ValueError("DATABASE_REQUIRED and DATABASE_URL are required in production")
        if not self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain the production frontend origin")
        if any(origin == "*" or origin.startswith("http://") for origin in self.cors_origins):
            raise ValueError("Production CORS origins must be explicit HTTPS origins")
        if "*" in self.trusted_hosts:
            raise ValueError("Production TRUSTED_HOSTS cannot contain a wildcard")
        if self.allow_sample_data:
            raise ValueError("ALLOW_SAMPLE_DATA must be false in production")
        if self.postgres_password == "curbo_password":
            raise ValueError("The default PostgreSQL password is forbidden in production")
        return self

    @property
    def project_root(self) -> Path:
        """
        Walk up from this file to find the repo root by looking for the
        data/sample sentinel directory.  This handles three layouts:
          • local dev:  CURBO/backend/app/config.py  → parents[2] = CURBO/
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
