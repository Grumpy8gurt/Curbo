# CURBO

CURBO is a geospatial planning dashboard for reviewing streets, sidewalk ramps, fire hydrants, bicycle facilities, and field annotations around Eugene, Oregon.

It helps a reviewer select a road, inspect nearby infrastructure, create point or line notes, move those notes through a review workflow, and download an HTML corridor report. CURBO is a screening and collaboration tool—it does not determine legal compliance, safety, or project priority.

## Final Sprint 5 result

Sprint 5 stabilized the complete application and prepared the repository for engineering handoff. The final work adds transactional persistence, safe retries and concurrent updates, production configuration checks, API security foundations, improved spatial calculations, explicit frontend failure behavior, dependency and bundle checks, hardened containers, CI, database migrations, backup/restore tools, and complete verification documentation.

The repository is suitable for local development and demonstration. Before an internet-facing customer launch, it still needs real organizational login and tenant authorization, a managed HTTPS deployment, operated monitoring and backups, complete authoritative datasets, and load/security/accessibility testing. See [Production remediation status](docs/production-remediation-status.md).

## Fastest way to run it

Requirements:

- Docker Desktop
- Git

From a terminal:

```bash
git clone https://github.com/Grumpy8gurt/Curbo.git
cd Curbo
cp .env.example .env
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173).

Stop the project with:

```bash
docker compose down
```

The normal Docker start runs the frontend and backend with persistent local volumes. It does not start PostgreSQL unless the optional `database` profile and `DATABASE_URL` are configured.

## Run it in VS Code

Open the `Curbo` folder in VS Code and create two terminals. The two terminals are needed because the backend and frontend are separate programs and both must stay running.

Terminal 1—backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2—frontend:

```bash
cd frontend
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The backend API is available at [http://localhost:8000/docs](http://localhost:8000/docs).

If the terminal shows both `(base)` and `(.venv)`, confirm the project Python is active:

```bash
which python
```

The result should end in `Curbo/backend/.venv/bin/python`.

## Run the tests

After installing the backend and frontend dependencies, run every Sprint 5 check from the repository root:

```bash
./scripts/verify_sprint5.sh
```

This runs backend and frontend tests, both dependency audits, the production frontend build and bundle budget, GeoJSON validation, an Alembic migration round trip, and Docker Compose validation.

Run one backend test file:

```bash
cd backend
.venv/bin/python -m pytest tests/test_layers.py -q
```

Run one frontend test file:

```bash
cd frontend
npm test -- src/api/annotations.test.ts
```

The final verified baseline is 45 backend tests and 15 frontend tests. See [Manual verification](docs/manual-verification.md) for the recorded evidence.

## Main workflow

1. The frontend loads cached Eugene infrastructure from the backend.
2. A reviewer searches for and selects a road corridor.
3. The backend calculates nearby infrastructure and active reviewer concerns.
4. The reviewer creates a point or line annotation.
5. The backend saves it with a unique ID and version.
6. The reviewer can move it from `pending` to `reviewed`, `confirmed`, or `rejected`.
7. A report captures the current corridor evidence, notes, signals, and limitations.

In normal use, the server must confirm a write before the frontend says it was saved. Invalid coordinates, oversized geometry, invalid status changes, stale versions, unsupported report formats, and unauthorized requests return clear errors without silently changing stored data.

## Architecture

```text
React + TypeScript + MapLibre frontend
                 |
                 | /api/v1
                 v
FastAPI + Pydantic service
       |                 |
       |                 +--> cached Eugene GeoJSON layers
       |
       +--> PostgreSQL transactions in production
       +--> locked JSON file for simple local development
       +--> retained HTML corridor reports
```

Major software:

- Frontend: React, TypeScript, Vite, MapLibre, Vitest, and Testing Library.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, and pytest.
- Data: cached GeoJSON from City of Eugene GIS.
- Runtime: Nginx, Docker Compose, and optional PostgreSQL/PostGIS.
- Quality: GitHub Actions, npm audit, pip-audit, bundle budgets, and data validation.

Read [Architecture](docs/architecture.md) for component boundaries and design decisions and [Requirements](docs/requirements.md) for implemented and remaining requirements.

## Project structure

```text
Curbo/
├── backend/            FastAPI application, persistence, migrations, and tests
├── frontend/           React application, API clients, components, and tests
├── data/               Eugene cache and compact sample GeoJSON
├── docs/               product, architecture, verification, and review records
├── scripts/            verification, data refresh, backup, and restore tools
├── .github/workflows/  continuous-integration checks
└── docker-compose.yml  local frontend/backend/database orchestration
```

## Data and mock behavior

The committed `data/eugene/` cache lets the project run without calling an external GIS service at startup. Roads contain a complete 13,520-feature snapshot captured July 27, 2026; other layers are bounded demonstration extracts and must not be described as complete or current.

Refresh and validate cached data with:

```bash
python scripts/fetch_eugene_data.py --layer roads
python scripts/validate_geojson.py
```

The frontend uses the real API by default. `VITE_USE_MOCK_API=true` is only for an intentional, visibly labeled frontend demonstration. A network failure never activates mock mode and never produces a false saved state.

## Security and production note

Local development is intentionally convenient. Production mode is deliberately strict: startup requires authentication, a strong API key, PostgreSQL, current migrations, explicit HTTPS origins and trusted hosts, and production-ready data. The API-key layer is a foundation, not a replacement for OIDC, organizations, roles, and record-level authorization.

Deployment, migrations, monitoring, backup, restore, rollback, and incident guidance are in the [Operations runbook](docs/operations-runbook.md).

## Documentation

- [Project vision](docs/project-vision.md)
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Data model](docs/data-model.md)
- [Manual verification](docs/manual-verification.md)
- [AI implementation review](docs/ai-implementation-review.md)
- [Production readiness audit](docs/production-readiness-audit.md)
- [Production remediation status](docs/production-remediation-status.md)

## Sprint history and submission

The Git history preserves the prototype, Eugene GIS integration, annotation review workflow, production-readiness audit, remediation, and final documentation as separate meaningful steps.

- GitHub repository: https://github.com/Grumpy8gurt/Curbo
- Sprint 2 branch: `sprint-2-prototype`
- Sprint 3 branch: `sprint-3-prototype`
- Sprint 4 branch: `sprint-4-milestone`
- Final Sprint 5 branch: `sprint-5-final`
- Sprint 5 merged into `main`: **Yes**
- Instructor access: `pcolbert-uo` retains repository access

Submission summary: CURBO is a full-stack Eugene mobility-planning dashboard that combines cached civic GIS data with persistent reviewer annotations, status-aware corridor analysis, and downloadable HTML reports. Sprint 5 stabilizes persistence and failure handling, adds production safety and operations foundations, and records repeatable automated and manual verification for future engineers.
