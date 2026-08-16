# CURBO AI Implementation Review

## Responsible-use statement

AI assistance was used as an engineering aid throughout CURBO for repository inspection, test ideas, implementation drafts, failure investigation, refactoring suggestions, documentation, and verification commands.

AI output was not treated as automatically correct. Every accepted change was compared with the existing architecture and project scope, reviewed in the repository, and checked with automated tests, builds, audits, data validation, or manual service/browser behavior. Production claims that could not be proven were documented as remaining risks.

The student remains responsible for the product scope, engineering decisions, Git history, and submitted repository.

## Sprint 5 completed capability

The most important stabilized capability was durable annotation and report persistence.

Before remediation, two backend processes could generate the same sequential annotation ID and overwrite one another’s JSON-file changes. A failed write could also leave memory different from disk, and a frontend network failure could appear to the user as a successful browser-only save.

Sprint 5 completed a PostgreSQL transaction path for annotations and report metadata, UUID-based IDs, idempotent create requests, optimistic versions, lifecycle rules, migrations, durable report lookup, and a locked atomic JSON path for simple local development. The frontend now requires a successful server response before displaying saved state.

## Expected behavior

During normal use:

- creating an annotation returns one unique, durable annotation;
- retrying the same create with the same idempotency key returns that annotation instead of a duplicate;
- a valid status change updates the stored status and increments its version;
- restarted application instances can read the saved work;
- reports use unique IDs and remain downloadable after restart; and
- the frontend announces success only after the backend confirms it.

When input or conditions are invalid:

- bad geometry or extra fields return HTTP 422;
- unknown records return HTTP 404;
- stale versions or disallowed status changes return HTTP 409 without overwriting current state;
- unsupported report formats return HTTP 422;
- unavailable required databases make readiness fail and production startup stop; and
- network failure is shown as an error rather than a saved result.

## Test selection

Tests were chosen around the failures most likely to lose work, mislead users, or create unsafe production behavior:

- restart persistence proves data is not only stored in process memory;
- two-store concurrent writes reproduce the original lost-update defect;
- idempotency protects client retries after uncertain network results;
- stale versions protect one reviewer from overwriting another;
- invalid geometry, request limits, and source spoofing protect the trust boundary;
- report restart and retention tests protect durable, bounded artifacts;
- health failure tests protect deployment routing decisions;
- malformed-response and unreachable-API tests protect honest frontend state; and
- exact spatial tests protect corridor counts from rectangle and segment edge cases.

These tests focus on externally visible behavior instead of checking private implementation details unless the geometry helper itself is the behavior under review.

## Explain one test

`test_independent_stores_do_not_lose_concurrent_writes` in `backend/tests/test_persistence.py` directly protects the defect reproduced during the production audit.

- **Setup:** Create one temporary annotation file and two independent `AppStore` instances pointing to it. This represents separate backend instances with separate memory.
- **Action:** Use two worker threads to create different annotations at nearly the same time.
- **Expected result:** Each create receives a different ID, and neither valid annotation disappears.
- **Assertion:** The test verifies that there are two unique created IDs, reloads a third store from disk, and checks that the IDs on disk exactly equal both created IDs.

The test would fail if file locking, reload-before-write, UUID creation, or atomic publication were broken in a way that lost or replaced a writer’s record.

## Test value

The concurrent-store test protects real user work, not simply a code path. The audited version failed this scenario by reusing `ann_003` and allowing the second writer to replace the first. A regression to stale in-memory whole-file writes would make the final assertion fail.

The idempotency and stale-version tests protect the two other sides of concurrency: duplicate creates and lost updates. Together, they cover create retry, overlapping file writers, and conflicting status edits.

## Manual and automated evidence

Manual verification was used for behavior that depends on assembled services or human interpretation:

- real Docker frontend/backend startup and health;
- frontend-to-backend proxy behavior;
- visible create/reject/confirm workflow;
- saved status after restart;
- report readability;
- mobile layout and product language; and
- actual security and caching response headers.

Automation was used for rules that must be repeated exactly across many valid and invalid cases:

- persistence, concurrency, idempotency, and stale versions;
- lifecycle transitions and schema boundaries;
- authentication, body/rate limits, and database health;
- report format, path, restart, and retention behavior;
- frontend timeouts, errors, and runtime response validation;
- data normalization and spatial calculations;
- builds, dependency audits, migrations, and GeoJSON validation.

This division keeps manual evidence meaningful without relying on a person to reproduce every boundary case.

## AI-generated test decisions

### Accepted and revised

AI identified that collinear spatial segments were a missing edge case. The first intersection logic used orientation products and incorrectly treated all collinear segments as intersecting, even when they were separated. The idea was accepted, but the implementation was revised to require that a collinear point actually lie within the other segment’s bounds. A focused regression test asserts a positive distance for two separate collinear lines.

### Combined

Several proposed persistence checks were combined into focused groups rather than one large scenario. Restart persistence, concurrent file stores, idempotent create, and stale update each received a separate test. This produces clearer failures: a failed idempotency assertion does not hide whether restart persistence still works.

### Rejected

A proposed whole-application frontend unit test was rejected because it required extensive MapLibre/WebGL mocks and would mainly test the mocks. Smaller API and component tests protect exact behavior, while the real map workflow was checked manually in the browser.

AI suggestions to describe the repository as fully production-ready were also rejected. Repository hardening cannot substitute for OIDC tenant authorization, managed TLS and secrets, operated monitoring/backups, complete source data, or load/security/accessibility testing.

## Failure investigation

The most useful final failure came from the first hardened frontend container run. Nginx exited because it tried to change ownership of a temporary directory after the container had dropped all capabilities. The investigation showed that the security controls were working, but the image expected root startup behavior.

The fix was not to restore privileges. The frontend image now runs directly as the unprivileged `nginx` user, supplies a non-root main configuration, and mounts its temporary directories with matching ownership. The rebuilt container became healthy and passed static-file, proxy, security-header, and shutdown checks.

Another quality concern was documentation drift. The former architecture and data-model documents still said JSON was the only persistence path and automatic frontend fallback was normal. Those statements became dangerous after Sprint 5 changes, so the required documents and source comments were reconciled with the implementation.

## Refactoring

Important maintainability improvements include:

1. shared geometry-position validation for points and every LineString position;
2. one persistence service with explicit database and local-file paths;
3. one allowed-transition table for annotation lifecycle rules;
4. one frontend request function for timeout, headers, normalized errors, and runtime validation;
5. one road index and ETag computed at startup instead of repeated full scans/hashes;
6. isolated pure spatial and ramp-review helpers; and
7. a single `verify_sprint5.sh` entry point for the final quality baseline.

Expected behavior remained intact through 45 backend tests, 15 frontend tests, production builds, dependency audits, data validation, migration round trips, Compose checks, and live container smoke tests.

## Repository evidence

Repository quality improvement is visible through:

- preserved Sprint 2, Sprint 3, Sprint 4, and Sprint 5 branches;
- focused commits for application hardening, frontend reliability, and final documentation;
- backend and frontend test suites stored beside the implementation;
- GitHub Actions repeating the main checks on pushes and pull requests;
- an original production-readiness audit preserved as a historical record;
- a separate remediation-status document distinguishing fixed, partial, and external work;
- manual-verification notes that separate current service checks from earlier browser evidence;
- complete vision, requirements, architecture, API, data, and operations documents; and
- README instructions verified against the final structure.

No commit or test count is presented as proof that external production operations already exist. The repository records those items as blockers.

## Remaining risk

The largest remaining engineering concerns are:

- shared API-key authentication instead of OIDC users and tenant authorization;
- full-network downloads and linear in-memory spatial scans;
- incomplete non-road datasets;
- synchronous local HTML report storage;
- process-local rate limiting;
- no hosted monitoring, alerting, secret management, or operated backup schedule; and
- no complete browser E2E, assistive-technology, load, recovery, or penetration test suite.

These risks are detailed in `docs/production-remediation-status.md` and are intentionally not hidden behind the successful course-project verification result.

## Final assessment

AI materially accelerated review, implementation, and test coverage, but the strongest results came from checking its suggestions against real failures. The project demonstrates responsible AI-assisted engineering because accepted work has evidence, rejected work has a reason, limitations remain visible, and the final repository can be understood without relying on the AI conversation.
