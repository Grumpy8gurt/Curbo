# Production Remediation Status

**Updated:** August 15, 2026<br>
**Source audit:** [Production readiness audit](production-readiness-audit.md)

## Current decision

CURBO is substantially safer and more reliable than the audited version, but it is **not yet approved for an internet-facing production launch**. The repository now contains safe application defaults, transactional persistence support, repeatable builds, CI checks, hardened containers, and operating procedures. Production still requires an external identity/TLS boundary, tenant-level authorization, monitoring and alerts, operated backups, complete authoritative data, and scalability work.

## What was fixed

- Production startup fails closed unless authentication, a strong API key, PostgreSQL, trusted hosts, explicit HTTPS origins, and non-sample data are configured.
- Annotations and report metadata use transactional database operations when a database is configured. UUIDs, idempotency keys, version checks, lifecycle rules, constraints, indexes, and migrations are included.
- The development JSON fallback now uses process and thread locks, reload-before-write, atomic replacement, and post-persistence memory updates.
- Frontend network failures no longer pretend that writes succeeded. Mock data is opt-in and visibly labeled.
- Geometry, request bodies, and mutation rates are bounded. Reports have UUIDs, safe paths, atomic files, retention limits, and truthful HTML-only responses.
- Health and readiness return failure when a required database is unavailable.
- API v1 is canonical; hidden legacy aliases include deprecation headers.
- Data responses use runtime validation. Frontend requests time out and report normalized errors.
- Road responses support gzip, cache headers, and ETags. The initial UI bundle is code-split and budgeted, and the road selector no longer renders every road at once.
- Spatial distance checks now use segment geometry rather than bounding-box overlap alone.
- The refresh script requires approved HTTPS sources, validates temporary files, enforces minimum counts and size limits, records provenance, and publishes atomically.
- Dependencies are reproducibly locked and audited. Containers use digest-pinned images, non-root users, read-only filesystems, dropped capabilities, health checks, and loopback-only host ports.
- CI, backup/restore scripts, a deployment/incident runbook, security headers, request IDs, and structured request logs are present.

## Audit finding status

| Finding | Status | Result or remaining work |
| --- | --- | --- |
| PR-01 authentication and authorization | Partial | Production requires a strong API key and logs an actor. Replace the shared key with OIDC, organizations, roles, and record-level tenant checks before launch. |
| PR-02 concurrent JSON persistence | Fixed for intended operation | Production requires PostgreSQL transactions. The development file fallback is locked and atomic. |
| PR-03 false saved frontend state | Fixed | Mutations require server success; mock mode is explicit and labeled. |
| PR-04 unbounded writes | Mostly fixed | Body, geometry, rate, and report retention limits exist. Production should use gateway/distributed quotas and load testing. |
| PR-05 non-transactional retry behavior | Fixed | Database transactions, unique idempotency keys, optimistic versions, and safe file fallback are implemented. |
| PR-06 synthetic backend records | Fixed | New stores are empty; sample data requires explicit configuration. |
| PR-07 forged source values | Fixed | Client source input is rejected and server identity supplies the source. |
| PR-08 exposed database/default password | Fixed | No database host port is published and Compose requires an explicit password. |
| PR-09 secure web boundary | Partial/external | Same-origin proxying and security headers exist. Operate an identity-aware HTTPS gateway and managed secrets before launch. |
| PR-10 misleading health checks | Fixed | Liveness is process-only; health/readiness return 503 for a required unavailable database. |
| PR-11 unused database path | Fixed | Runtime annotations and report metadata use SQLAlchemy when configured; production requires it. |
| PR-12 database integrity/spatial design | Partial | Constraints, indexes, migrations, and versioning exist. PostGIS-native geometry and spatial indexes remain future work. |
| PR-13 report durability and bounds | Mostly fixed | Durable UUID report files, metadata, safe download paths, and retention exist. A background job/object-store design is still preferable at scale. |
| PR-14 oversized road download | Partial | Gzip and conditional caching reduce repeat traffic. Cold loads still need viewport queries or vector tiles. |
| PR-15 frontend large-list/render work | Mostly fixed | Search results are capped, map updates are separated, and map code is lazy-loaded. Full-network map rendering remains a scale risk. |
| PR-16 inaccurate and linear spatial analysis | Partial | Metric point/segment and segment/segment checks replaced rectangle-only results. Queries remain in-memory and linear. |
| PR-17 incomplete planning evidence | Partial | Production startup checks dataset status and minimum counts and the refresh records provenance. Authoritative dataset completeness and domain validation remain operational requirements. |
| PR-18 read fallback hides outages | Fixed | Fallback is explicit mock mode only and the UI identifies incomplete/mock data. |
| PR-19 unsafe data refresh | Mostly fixed | Allowlisting, HTTPS, limits, validation, provenance, atomic writes, and correct failure exits exist. Scheduled source monitoring is still needed. |
| PR-20 hanging/unvalidated frontend requests | Fixed | Requests have timeouts, normalized errors, content checks, and runtime payload validation. |
| PR-21 keyboard access | Improved/partial | The map can receive focus and keyboard placement, and manual entry remains available. Complete assistive-technology testing is still required. |
| PR-22 bundle control | Fixed | Map code is lazy-loaded and build-enforced JavaScript budgets are present. |
| PR-23 reproducible dependencies | Fixed | Exact production Python locks, npm lock use, dependency audits, and digest-pinned container bases are enforced. |
| PR-24 backend container hardening | Fixed | Non-root execution, read-only filesystems, limited temporary storage, dropped capabilities, and health checks are configured. |
| PR-25 CI/CD and rollback | Partial | CI and deploy/rollback instructions exist. Configure protected branches, environment promotion, artifact signing, and deployment automation in the hosting platform. |
| PR-26 incident visibility | Partial | Structured logs, request IDs, actor fields, and a runbook exist. Connect them to hosted metrics, logs, traces, alerting, and on-call ownership. |
| PR-27 backup/disaster recovery | Partial | Checked backup/restore commands and procedures exist. Schedule encrypted off-site backups, enable point-in-time recovery, and record a restore drill. |
| PR-28 production failure tests | Improved/partial | Tests now cover persistence races, idempotency, stale updates, DB health failure, limits, auth, spoofing, report restart/retention, malformed frontend data, caching, and spatial accuracy. Add browser E2E, real PostgreSQL concurrency, load, penetration, and recovery tests. |
| PR-29 API/workflow rules | Fixed | API v1, deprecation behavior, allowed lifecycle transitions, optimistic versions, and schema restrictions are defined and tested. |
| PR-30 browser policy | Fixed in application | Explicit CORS, no credential wildcard, trusted hosts, CSP, framing, MIME, referrer, and permissions headers are configured. The production gateway must preserve them. |

## Verification evidence

The following checks passed on August 15, 2026:

- Backend: **45 tests passed**.
- Frontend: **16 tests passed** across 8 test files.
- Production frontend TypeScript/build: passed.
- JavaScript bundle budgets: passed; initial application chunk is about 174 KB and the lazy map chunk is about 1,037 KB before gzip.
- npm audit: **0 known vulnerabilities**.
- Python dependency check: no broken requirements.
- Python production dependency audit: **0 known vulnerabilities**.
- GeoJSON validation: **7 of 7 files passed**.
- Alembic migration upgrade, downgrade, and re-upgrade: passed against SQLite during remediation verification.
- Docker Compose configuration: passed.
- Backend and frontend container builds: passed.
- Container smoke test: both services healthy; direct backend health, frontend health, frontend-to-backend proxying, annotations response, and browser security headers passed.
- Cache-only Eugene roads refresh: passed using the validated existing cache.

Run the ordinary repository checks with:

```bash
./scripts/verify_sprint5.sh
```

See [Operations runbook](operations-runbook.md) for deployment, migration, backup, restore, rollback, and incident procedures.

## Production launch blockers

Do not expose CURBO to paying customers until all of these are complete:

1. Deploy behind TLS with real OIDC identity and tenant/role/record authorization.
2. Use managed PostgreSQL with production migrations, encryption, point-in-time recovery, and a completed restore drill.
3. Verify authoritative datasets meet agreed coverage, freshness, and correctness standards.
4. Connect logs and health signals to monitoring, abuse alerts, and an owned on-call process.
5. Run real-PostgreSQL concurrency, browser E2E, accessibility, load, recovery, and security testing.
6. Replace full-network downloads and linear spatial scans before high-volume use.
