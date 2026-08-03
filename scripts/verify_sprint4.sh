#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_COMMAND="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_COMMAND}" >/dev/null 2>&1 && [[ ! -x "${PYTHON_COMMAND}" ]]; then
  echo "Python executable not found: ${PYTHON_COMMAND}" >&2
  exit 1
fi

echo "[1/6] Backend tests"
(
  cd "${PROJECT_ROOT}/backend"
  "${PYTHON_COMMAND}" -m pytest -q
)

echo "[2/6] Frontend tests"
(
  cd "${PROJECT_ROOT}/frontend"
  npm test
)

echo "[3/6] Frontend production build"
(
  cd "${PROJECT_ROOT}/frontend"
  npm run build
)

echo "[4/6] Frontend dependency audit"
(
  cd "${PROJECT_ROOT}/frontend"
  npm audit
)

echo "[5/6] GeoJSON validation"
(
  cd "${PROJECT_ROOT}"
  "${PYTHON_COMMAND}" scripts/validate_geojson.py
)

echo "[6/6] Docker Compose configuration"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  (
    cd "${PROJECT_ROOT}"
    docker compose config >/dev/null
  )
  echo "Docker Compose configuration is valid."
else
  echo "Skipped: Docker Compose is not installed or unavailable on this device."
fi

echo "Sprint 4 verification passed."
