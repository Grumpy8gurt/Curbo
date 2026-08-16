#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_COMMAND="${PYTHON_BIN:-${PROJECT_ROOT}/backend/.venv/bin/python}"

if [[ ! -x "${PYTHON_COMMAND}" ]]; then
  echo "Python executable not found: ${PYTHON_COMMAND}" >&2
  echo "Create backend/.venv and install backend/requirements-dev.txt first." >&2
  exit 1
fi

echo "[1/8] Backend tests"
(
  cd "${PROJECT_ROOT}/backend"
  "${PYTHON_COMMAND}" -m pytest -q
)

echo "[2/8] Python dependency checks"
"${PYTHON_COMMAND}" -m pip check
"${PYTHON_COMMAND}" -m pip_audit -r "${PROJECT_ROOT}/backend/requirements.lock"

echo "[3/8] Frontend tests"
(
  cd "${PROJECT_ROOT}/frontend"
  npm test
)

echo "[4/8] Frontend production build and bundle budget"
(
  cd "${PROJECT_ROOT}/frontend"
  npm run build
)

echo "[5/8] Frontend dependency audit"
(
  cd "${PROJECT_ROOT}/frontend"
  npm audit
)

echo "[6/8] GeoJSON validation"
(
  cd "${PROJECT_ROOT}"
  "${PYTHON_COMMAND}" scripts/validate_geojson.py
)

echo "[7/8] Database migration round trip"
MIGRATION_DIR="$(mktemp -d)"
trap 'rm -rf "${MIGRATION_DIR}"' EXIT
(
  cd "${PROJECT_ROOT}/backend"
  export DATABASE_URL="sqlite:///${MIGRATION_DIR}/migration-test.db"
  "${PYTHON_COMMAND}" -m alembic upgrade head
  "${PYTHON_COMMAND}" -m alembic downgrade base
  "${PYTHON_COMMAND}" -m alembic upgrade head
)

echo "[8/8] Docker Compose configuration"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  (
    cd "${PROJECT_ROOT}"
    docker compose config --quiet
  )
  echo "Docker Compose configuration is valid."
else
  echo "Skipped: Docker Compose is not installed or unavailable on this device."
fi

echo "Sprint 5 verification passed."
