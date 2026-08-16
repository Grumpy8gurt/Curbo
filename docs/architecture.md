# CURBO Architecture

## Overview

CURBO is a two-service web application:

- a React frontend displays the map and reviewer workflow;
- a FastAPI backend validates requests, serves GIS layers, performs corridor analysis, persists reviewer work, and creates reports.

Cached civic data is read from GeoJSON. Writable annotation and report metadata use PostgreSQL when configured. A locked JSON annotation file is retained for simple local development.

```text
Browser
  |
  | HTTP /api/v1
  v
Nginx frontend container
  |-- serves built React files
  +-- proxies /api to FastAPI
                    |
                    +-- cached Eugene GeoJSON (read-only runtime layers)
                    +-- PostgreSQL (production annotations/report metadata)
                    +-- locked JSON (local annotation fallback)
                    +-- retained HTML report files
```

## Main software

| Area | Software | Responsibility |
| --- | --- | --- |
| Browser UI | React and TypeScript | Application state, forms, panels, review workflow, and error display. |
| Map | MapLibre GL | Roads, point features, line features, selections, and drawing interactions. |
| Frontend tooling | Vite, Vitest, Testing Library | Development server, production build, component/API tests, and code splitting. |
| API | FastAPI and Pydantic | Routing, validation, OpenAPI, dependency injection, and response models. |
| Persistence | SQLAlchemy and Alembic | Database transactions, models, schema migrations, and revision checks. |
| Production database | PostgreSQL | Durable annotation and report metadata storage. PostGIS is available as the container base but GIS layers are not yet imported into spatial tables. |
| Local data | GeoJSON and JSON | Cached Eugene GIS layers and local-development annotations. |
| Web serving | Nginx | Static frontend assets, same-origin API proxy, request-size limit, and browser security headers. |
| Packaging | Docker Compose | Repeatable frontend/backend startup and an optional database profile. |
| Quality | pytest, npm audit, pip-audit, GitHub Actions | Regression, dependency, migration, build, data, and container checks. |

## Repository boundaries

### `frontend/`

The frontend owns presentation and browser interaction. It:

- loads runtime data through typed API modules;
- validates important server response shapes at runtime;
- displays explicit loading, unavailable, error, and mock states;
- renders infrastructure and annotations in MapLibre;
- searches roads without creating 13,520 DOM options;
- creates point or line annotation requests;
- includes the current annotation version in status changes;
- refreshes corridor evidence after confirmed writes;
- invalidates stale report links; and
- lazy-loads the large map bundle.

The frontend never decides that a network failure is a successful save. Mock data is used only when `VITE_USE_MOCK_API=true`, and the interface labels that mode.

### `backend/app/routers/`

Routers translate HTTP requests and responses:

- `health.py`: public health, liveness, and readiness probes;
- `layers.py`: cached GeoJSON layers, optional bounding boxes, road ETags, and caching;
- `annotations.py`: list, create, and status update workflows;
- `corridors.py`: selected-road analysis; and
- `reports.py`: HTML report creation and safe download.

The canonical data prefix is `/api/v1`. Temporary legacy `/api` aliases are hidden from OpenAPI and include deprecation headers. Health probes remain under `/api`.

### `backend/app/schemas/`

Pydantic schemas enforce the API contract. They validate:

- known annotation and lifecycle values;
- descriptions and extra fields;
- finite longitude and latitude ranges;
- Point and LineString shape;
- a maximum of 1,000 line positions;
- ordered and in-range bounding boxes;
- expected annotation versions; and
- HTML-only reports.

### `backend/app/services/`

- `eugene_data_service.py` loads and normalizes source-specific GIS properties.
- `app_store.py` provides indexed road lookup, annotation/report persistence, idempotency, and optimistic version rules.
- `spatial_queries.py` performs bounding-box prefiltering followed by point-to-segment and segment-to-segment metric distance checks.
- `report_generator.py` renders escaped HTML and prunes expired/excess report files.

### `backend/app/models/` and `backend/migrations/`

SQLAlchemy models describe annotations and report metadata. The migration creates:

- status and format constraints;
- useful type, status, road, and creation-time indexes;
- unique idempotency keys;
- optimistic version fields; and
- durable report download metadata.

Production never creates tables during web-server startup. Alembic must apply the expected revision first, and startup rejects a missing or stale revision.

### `data/`

- `data/eugene/` contains the normal offline cache.
- `data/sample/` contains small, obvious development fallbacks.

The application does not call live City services during normal startup. Data refresh is a separate script with HTTPS source allowlisting, size limits, minimum counts, validation, provenance metadata, temporary files, filesystem synchronization, and atomic replacement.

## Request flow

### Read a layer

```text
React API module
  -> GET /api/v1/layers/roads
  -> authentication dependency when enabled
  -> road collection in AppStore
  -> optional bbox filtering
  -> ETag/cache response
  -> GZip middleware for large response
  -> runtime frontend validation
  -> MapLibre source
```

### Create an annotation

```text
Annotation form
  -> POST /api/v1/annotations + Idempotency-Key
  -> body/rate/authentication checks
  -> Pydantic geometry and field validation
  -> PostgreSQL transaction OR locked local-file update
  -> server UUID, source, timestamp, and version
  -> confirmed response
  -> frontend shows saved state and refreshes corridor
```

If validation, authorization, persistence, or the network fails, the frontend shows an error and does not insert a browser-only saved record.

### Update annotation status

```text
Selected annotation + expectedVersion
  -> PATCH /api/v1/annotations/{id}
  -> lifecycle rule check
  -> compare current version
  -> update status and increment version in one transaction
  -> HTTP 409 for stale version or invalid transition
  -> refresh corridor only after success
```

### Generate a report

```text
Selected road
  -> fresh corridor analysis
  -> escaped HTML report written atomically
  -> database/file metadata with UUID
  -> retention pruning
  -> safe report-specific download route
```

## Persistence design

### PostgreSQL path

When `DATABASE_URL` is configured, annotation and report metadata operations use short SQLAlchemy sessions and commit or roll back as a unit. UUID-based IDs prevent cross-process counter collisions. Unique idempotency keys make retries safe. Version comparisons prevent one reviewer from silently overwriting a newer status.

Production requires this path and the exact Alembic revision.

### Local JSON path

When no database is configured, annotations use an inspectable JSON file. The store:

1. acquires a shared thread lock;
2. acquires an operating-system lock for the target file;
3. reloads the latest stored records;
4. applies the candidate change to a copy;
5. writes a unique temporary file;
6. flushes and synchronizes it;
7. atomically replaces the prior file; and
8. updates memory only after persistence succeeds.

This supports a safe local demo but is not the intended high-scale production data store.

## Security boundary

The backend provides:

- production fail-closed configuration;
- constant-time API-key comparison;
- trusted-host and explicit CORS configuration;
- body and mutation limits;
- server-owned annotation source values;
- safe report paths;
- request IDs and structured logs;
- API security headers; and
- dependency and container checks.

The frontend Nginx container provides a same-origin proxy, a 1 MB request limit, CSP, framing protection, MIME protection, referrer policy, and permissions policy.

The current API key represents one deployment identity. It does not provide individual users, organizations, roles, tenant isolation, or record-level permissions. Those require an identity-aware HTTPS gateway and backend authorization before production use.

## Container and deployment design

- Backend and frontend images use digest-pinned bases.
- Application processes run as non-root users.
- Compose filesystems are read-only except named data volumes and limited temporary filesystems.
- Linux capabilities are dropped and privilege escalation is disabled.
- Host ports bind only to loopback for local development.
- Frontend waits for backend readiness.
- PostgreSQL has no host port and is enabled only through the `database` profile.

GitHub Actions installs from lock files and runs backend/frontend tests, dependency audits, a frontend production build, bundle checks, a migration round trip, GeoJSON validation, Compose validation, and both container builds.

## Important design decisions

### Separate frontend and backend processes

React/Vite and FastAPI have different runtimes and development reloaders. Keeping them separate makes each responsibility clear and allows the same API to serve other clients. Two terminals are required for direct development because both long-running programs must remain active.

### Cached data instead of startup network calls

The application stays demonstrable when the City service is unavailable, and a refresh cannot unexpectedly change runtime data. The tradeoff is that freshness must be operated and documented.

### Explicit mock mode

Automatic fallback hid outages and could lose reviewer work. Sprint 5 keeps mock data useful for demonstrations but makes it an intentional configuration with visible UI labeling.

### PostgreSQL for writes, GeoJSON for current read layers

Transactional reviewer work was the urgent integrity problem. Moving every GIS layer into PostGIS would be a larger data-platform change, so Sprint 5 stores writes safely while keeping the verified offline layer cache.

### Screening language

Available datasets cannot support an authoritative safety, compliance, or priority conclusion. The backend returns evidence, review attention, planning notes, and an explicit limitation instead.

## Known architectural limits

- Cold map loads still transfer the complete road network.
- MapLibre still renders the complete selected layer collections.
- Spatial queries use an in-memory prefilter and linear scan rather than PostGIS indexes.
- The non-road Eugene layers are bounded demonstration extracts.
- HTML report generation is synchronous and locally stored.
- Rate limiting is process-local rather than gateway/distributed.
- Authentication is a shared API-key foundation, not multi-user authorization.
- Hosted monitoring, secret management, backups, and disaster recovery must be operated outside this repository.

These limits and their launch implications are tracked in [Production remediation status](production-remediation-status.md).
