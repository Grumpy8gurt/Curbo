# CURBO Requirements

This document describes the final Sprint 5 implementation. “Implemented” means the behavior exists and has repository evidence. “Partial” means a useful foundation exists but additional production work is required. “Future” is intentionally outside the completed course-project scope.

## Functional requirements

| ID | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| FR-01 | Display Eugene roads, sidewalk ramps, hydrants, bicycle facilities, and reviewer annotations on a map. | Implemented | Layer API routes, `MapView`, layer tests, browser verification. |
| FR-02 | Let a user search for and select a road corridor. | Implemented | Searchable `CorridorSelector` capped at 50 displayed results. |
| FR-03 | Analyze infrastructure and reviewer notes near the selected corridor. | Implemented | Corridor API and metric geometry tests. |
| FR-04 | Create point and line reviewer annotations with a type and description. | Implemented | Annotation form, POST route, schema and API tests. |
| FR-05 | Persist annotations across a backend restart. | Implemented | PostgreSQL transaction path, locked JSON development path, restart tests. |
| FR-06 | Move annotations through `pending`, `reviewed`, `confirmed`, or `rejected` according to allowed transitions. | Implemented | PATCH route, popup control, lifecycle and conflict tests. |
| FR-07 | Exclude rejected annotations from active concern counts while preserving them in history. | Implemented | Status-aware corridor logic and tests. |
| FR-08 | Generate and download a readable corridor report. | Implemented | HTML report generator, durable metadata, safe download and restart tests. |
| FR-09 | Show available curb-ramp dimensions with units and screening limitations. | Implemented | Eugene normalization, popup helper, backend/frontend tests. |
| FR-10 | Run without a live external GIS request by using a committed cache. | Implemented | `data/eugene`, cache-only refresh and validation checks. |
| FR-11 | Allow an explicit frontend-only mock demonstration without silently entering mock mode. | Implemented | `VITE_USE_MOCK_API`, visible label, API-client tests. |
| FR-12 | Provide health, liveness, and readiness probes. | Implemented | `/api/health`, `/api/live`, `/api/ready`, dependency-failure tests. |
| FR-13 | Provide organization login, roles, tenant boundaries, and record ownership. | Partial | Shared API-key production guard exists; OIDC and tenant authorization remain required before multi-user launch. |
| FR-14 | Delete annotations or edit existing annotation geometry. | Future | Not included because product and audit-history rules are not defined. |
| FR-15 | Produce PDF reports. | Future | The API deliberately accepts HTML only. |

## Validation and failure requirements

| ID | Requirement | Expected behavior | Evidence |
| --- | --- | --- | --- |
| VR-01 | Validate GeoJSON coordinates. | Reject non-finite or out-of-range longitude/latitude with HTTP 422. | Annotation and layer tests. |
| VR-02 | Limit line size. | Reject LineStrings with more than 1,000 positions. | Production-safety tests. |
| VR-03 | Bound request size and mutations. | Return 413 for declared oversized bodies and 429 when the local mutation limit is exceeded. | Middleware tests. |
| VR-04 | Prevent forged sources. | Reject a client-supplied annotation `source`; assign the server-side reviewer source. | Annotation tests. |
| VR-05 | Make create retries safe. | A repeated valid `Idempotency-Key` returns the original record instead of a duplicate. | Persistence tests. |
| VR-06 | Prevent lost updates. | A stale `expectedVersion` returns HTTP 409 and does not overwrite current state. | Annotation conflict tests. |
| VR-07 | Enforce lifecycle rules. | Unsupported status transitions return HTTP 409. Unknown IDs return 404. | Annotation tests. |
| VR-08 | Reject unsupported reports. | Any format other than `html` returns validation failure. | Report tests. |
| VR-09 | Expose service failure honestly. | A required unavailable database makes readiness/health fail and prevents production startup. | Health and production-safety tests. |
| VR-10 | Reject malformed frontend responses. | The frontend shows an API error rather than trusting invalid JSON shapes. | API validation tests. |
| VR-11 | Never fake a successful write. | Network failure rejects the mutation and does not show a saved result. | Frontend API tests and manual failure review. |

## Persistence requirements

### Production mode

- PostgreSQL and current Alembic migrations are required.
- Annotation and report metadata writes use database transactions.
- Annotation IDs and report IDs are collision-resistant UUID-based values.
- Annotation creates support unique idempotency keys.
- Annotation updates use optimistic versions.
- Database status is included in readiness behavior.

### Local development mode

- PostgreSQL is optional.
- Annotation JSON writes use a shared thread lock and operating-system file lock.
- Each write reloads the latest file before changing it.
- A unique temporary file is flushed, synchronized, and atomically replaces the old file.
- In-memory state changes only after persistence succeeds.
- A missing annotation file starts empty; normal startup does not invent reviewer records.

## Non-functional requirements

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-01 | A new developer can run the project from the README. | Implemented and manually verified with Docker and direct development commands. |
| NFR-02 | The application has repeatable dependency installation. | Implemented with npm lock and exact Python production/dev lock files. |
| NFR-03 | Security dependency audits are part of verification and CI. | Implemented with npm audit and pip-audit. |
| NFR-04 | The initial frontend bundle has an enforced budget and heavy map code is lazy-loaded. | Implemented. |
| NFR-05 | Large road responses support compression and conditional caching. | Implemented with gzip, cache headers, and ETags. |
| NFR-06 | Containers run with restricted privileges. | Implemented with non-root users, read-only filesystems, dropped capabilities, limited temporary storage, and loopback ports. |
| NFR-07 | Production configuration fails closed. | Implemented for API key, database, HTTPS origins, trusted hosts, sample data, and default password checks. |
| NFR-08 | Requests can be traced without logging secrets. | Implemented with request IDs and structured request logs. External aggregation remains operational work. |
| NFR-09 | CI runs tests, builds, audits, migrations, data validation, Compose validation, and image builds. | Implemented in GitHub Actions. |
| NFR-10 | Backup, restore, rollback, and incident procedures are documented. | Implemented as scripts and a runbook; scheduling and restore drills remain external work. |
| NFR-11 | Common map input has a keyboard alternative. | Partially implemented with a focusable map, keyboard center placement, and manual coordinate entry. Full assistive-technology verification remains. |
| NFR-12 | Support high-volume citywide or multi-tenant production traffic. | Partial. Cold road downloads, full map rendering, and in-memory linear spatial scans must be replaced before scale. |

## Data requirements

- Every layer is a valid GeoJSON `FeatureCollection`.
- Source-specific fields are normalized into a stable frontend contract.
- Invalid or null source features are not allowed to crash the runtime.
- Production can require minimum layer counts and `cached-eugene` status.
- Refreshes use allowlisted HTTPS sources, response-size limits, temporary validation, provenance metadata, and atomic publication.
- Cached data remains screening evidence. Roads are a dated complete snapshot; the other committed Eugene collections are bounded extracts.

## Security and deployment requirements before production

The repository provides foundations but does not satisfy these external launch requirements by itself:

1. identity-aware HTTPS ingress;
2. OIDC validation, organizations, roles, and record-level authorization;
3. managed secrets and private encrypted PostgreSQL networking;
4. centralized logs, metrics, traces, abuse alerts, and on-call ownership;
5. encrypted off-site backups, point-in-time recovery, and a recorded restore drill;
6. authoritative data ownership and freshness agreements; and
7. browser E2E, accessibility, load, recovery, and penetration testing.

## Acceptance baseline

The final repository baseline is:

- 45 passing backend tests;
- 16 passing frontend tests;
- passing TypeScript and production frontend build;
- passing JavaScript bundle budgets;
- zero known npm or Python production dependency vulnerabilities at final verification;
- 7 of 7 GeoJSON files valid;
- successful Alembic upgrade/downgrade/upgrade;
- valid Docker Compose configuration; and
- healthy backend/frontend container smoke tests.
