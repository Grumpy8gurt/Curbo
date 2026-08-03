#!/usr/bin/env bash

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found on PATH."
  echo "Install Docker Desktop or another Docker runtime, then rerun this script."
  exit 1
fi

echo "Starting local development dependencies for CURBO..."
echo "This scaffold currently provisions only the PostGIS database."
echo "Frontend and backend services can be started using their local development instructions."

docker compose --profile database up -d postgres

echo "Postgres should now be starting on port 5432."
echo "Copy .env.example to .env if you need to customize credentials or ports."
