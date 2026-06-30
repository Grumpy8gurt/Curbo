# Curbo

**Serious name:** Sidewalk Surveying and Management Dashboard

Curbo is a geospatial planning dashboard for city planners, civil engineers, transportation planners, and surveyors. It is meant to be a practical workspace for inspecting street infrastructure, reviewing spatial data, and coordinating curb accessibility decisions.

## MVP Goal

The MVP is a map-first dashboard that can display street infrastructure layers, support basic spatial queries, store planner annotations, accept street-level image uploads, run a mocked curb-cut detection workflow, and generate corridor summary outputs later in the roadmap.

## High-Level Architecture

- `frontend/`: React + TypeScript map dashboard and operator workflows
- `backend/`: FastAPI application exposing GeoJSON and annotation APIs
- `ml/`: Python-based curb-cut detection service, initially mockable
- `postgres` + PostGIS: spatial data persistence and query engine
- `data/`: sample GeoJSON and future import datasets
- `docs/`: architecture, API planning, data model notes, and agent coordination

## Expected Tech Stack

- Frontend: React, TypeScript, modern mapping library
- Backend: FastAPI, Pydantic, SQLAlchemy or equivalent
- Database: PostgreSQL with PostGIS
- ML: Python inference service with mocked-first integration
- Local development: Docker Compose
- Data interchange: GeoJSON

## Local Development

The application code is not implemented yet, but the repo is prepared for future agents.

1. Copy `.env.example` to `.env`.
2. Review `docker-compose.yml`.
3. Run `./scripts/setup.sh` to start the PostGIS database container.
4. Future agents will add service-specific startup commands for `frontend/`, `backend/`, and `ml/`.

## Repository Layout

- `docs/`: planning and integration documents
- `frontend/`: future React app
- `backend/`: future FastAPI service
- `ml/`: future detection service
- `data/`: sample GeoJSON and later import-ready datasets
- `scripts/`: bootstrap and developer utility scripts
- `tests/`: cross-project and integration test home

## Agent Workflow Expectations

This repository starts as a clean monorepo scaffold. The intended workflow is:

- Initial Repository Agent establishes structure, shared docs, and sample data.
- Frontend Agent builds the dashboard UI and map interactions.
- Backend Agent builds API endpoints, persistence, and spatial services.
- ML Agent builds the curb-cut detection service and mockable integration boundary.
- Supervisor/Integration Agent connects everything, resolves contract drift, and validates end-to-end behavior.

Each agent should respect the documented boundaries and avoid overwriting unrelated work unless coordination requires it.
