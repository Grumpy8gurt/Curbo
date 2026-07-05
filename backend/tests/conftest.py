from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    settings = Settings(
        database_url="sqlite://",
        upload_dir=str(tmp_path / "uploads"),
        report_dir=str(tmp_path / "reports"),
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
