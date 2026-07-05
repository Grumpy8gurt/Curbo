from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ML_ROOT = Path(__file__).resolve().parents[1]
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

from app.main import create_app


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
