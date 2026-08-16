# CURBO Project Vision

## Purpose

CURBO gives transportation and public-works reviewers one clear place to inspect street context, record field observations, review those observations, and produce a simple corridor evidence report.

The project began as a prototype and evolved across the course into a complete full-stack application with local civic data, persistent workflows, automated tests, deployment foundations, and documented engineering limits.

## Problem

Street and curb planning often requires information from several maps, inventories, field notes, and review conversations. That information can be difficult to compare and easy to lose. A reviewer needs to understand what infrastructure is recorded near a corridor, add observations that are not in the inventory, track whether those observations were reviewed, and share the evidence without overstating what the data proves.

## Users

Primary users are:

- transportation planners;
- public-works and accessibility staff;
- field reviewers;
- project engineers; and
- future developers maintaining the application.

The current repository is a local demonstration and engineering foundation. A real multi-organization deployment requires stronger identity and tenant isolation than the included API-key safeguard.

## Product promise

CURBO should help a reviewer answer:

- Which road corridor am I reviewing?
- Which ramps, hydrants, and bicycle facilities are recorded nearby?
- What observations have reviewers added?
- Which observations still need review?
- Which observations were confirmed or rejected?
- What evidence and limitations should appear in a corridor report?

CURBO must not claim that its output determines accessibility compliance, corridor safety, legal eligibility, or project priority. Its results are screening evidence that supports professional review.

## Final Sprint 5 scope

The completed application includes:

- a React and MapLibre map focused on Eugene, Oregon;
- cached and normalized roads, sidewalk ramps, hydrants, and bicycle facilities;
- searchable corridor selection;
- point and line annotations;
- persistent annotation status workflow;
- status-aware corridor metrics and human-readable review signals;
- HTML corridor reports;
- PostgreSQL-backed annotation and report metadata persistence when configured;
- a safe locked JSON mode for simple local development;
- API validation, timeouts, idempotency, optimistic version checks, and lifecycle rules;
- automated backend, frontend, dependency, migration, build, and data checks;
- hardened container definitions, CI, backup/restore tools, and an operations runbook; and
- transparent manual-verification and AI-assistance records.

## Product principles

### Evidence before conclusions

Show the recorded facts, their source, their review status, and their limitations. Do not turn incomplete data into an authoritative safety or compliance score.

### Honest failure behavior

The interface must never describe browser-only fallback data as a successful server write. Unavailable services and invalid responses should be visible to the user.

### Durable reviewer work

Normal production writes should be transactional, uniquely identified, safe to retry, and protected from stale updates. Local file persistence should fail without corrupting the previous valid state.

### Offline-friendly civic data

Normal startup should use a validated local cache instead of depending on a live City service. Refreshing the cache is a separate, controlled operation.

### Simple handoff

Another developer should be able to clone the repository, run it from the README, understand its boundaries, run its verification checks, and identify the next production tasks.

## Success criteria

Sprint 5 is successful when:

1. the documented local start works;
2. a reviewer can inspect data, create an annotation, update its status, and generate a report;
3. saved review state survives restart;
4. invalid or stale requests fail clearly without an incorrect stored change;
5. automated and manual evidence demonstrate the expected behavior;
6. the implementation, documentation, and API contract agree;
7. earlier sprint branches and meaningful commits remain visible; and
8. unresolved production risks are documented instead of hidden.

## Deliberately excluded

The final course project does not include:

- legal accessibility determinations;
- project ranking or safety scoring;
- live crash, traffic-volume, speed, exposure, parking, or right-of-way feeds;
- routing or network optimization;
- image upload or machine-learning inference;
- PDF generation;
- organization-level login and tenant administration; or
- a hosted production environment.

These are separate product and governance projects, not safe assumptions to add to a prototype.

## Future direction

The next engineering phase should:

1. add OIDC login, organizations, roles, and record-level authorization;
2. deploy through managed HTTPS with managed secrets and PostgreSQL;
3. establish authoritative dataset ownership, completeness, and refresh targets;
4. move large GIS layers to viewport APIs, vector tiles, and PostGIS spatial indexes;
5. operate monitoring, alerting, backups, point-in-time recovery, and restore drills; and
6. complete browser E2E, assistive-technology, load, recovery, and security testing.
