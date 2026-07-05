from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "curbo-backend"
    version: str = "0.1.0"
    postgres_db: str = "ssm"
    postgres_user: str = "ssm_user"
    postgres_password: str = "ssm_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    backend_port: int = 8000
    upload_dir: str = "uploads"
    report_dir: str = "generated_reports"
    database_url: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def sample_data_dir(self) -> Path:
        return self.project_root / "data" / "sample"

    @property
    def resolved_upload_dir(self) -> Path:
        upload_path = Path(self.upload_dir)
        if upload_path.is_absolute():
            return upload_path
        return self.backend_root / upload_path

    @property
    def resolved_report_dir(self) -> Path:
        report_path = Path(self.report_dir)
        if report_path.is_absolute():
            return report_path
        return self.backend_root / report_path

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            "postgresql+psycopg2://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
