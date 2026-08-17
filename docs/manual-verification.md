# CURBO Manual Verification

This document separates checks performed against a running application from repeatable automated checks. Manual verification answers “does the assembled system behave correctly?” Automated verification protects exact rules and regressions.

## Final verification baseline

**Final verification dates:** August 15–17, 2026

**Final branch:** `sprint-5-final`
**Environment:** macOS, Docker Desktop, Python 3.13 virtual environment, Node 22 toolchain

## Sprint 5 manual service verification

The final frontend and backend images were built and started together with Docker Compose. The test containers were stopped after verification; their named data volumes were preserved.

| Manual check | Expected behavior | Observed result | Status |
| --- | --- | --- | --- |
| Start from Compose | Frontend waits for a healthy backend and both services become healthy. | `curbo-backend-1` and `curbo-frontend-1` both reported healthy. | Pass |
| Direct backend health | `/api/health` returns the backend service status. | HTTP 200 with `{"status":"ok","service":"curbo-backend"}`. | Pass |
| Frontend health | `/healthz` confirms that Nginx is serving. | HTTP 200 with `ok`. | Pass |
| Same-origin API proxy | The frontend container forwards `/api/health` to FastAPI. | HTTP 200 with the backend health payload. | Pass |
| Frontend document | The production server returns the CURBO application. | HTTP 200 and `<title>CURBO`. | Pass |
| Real annotation collection | A new local store starts empty instead of inventing reviewer data. | `/api/v1/annotations` returned zero features. | Pass |
| Invalid coordinate | Impossible longitude is rejected without creating a record. | Longitude `999` returned HTTP 422. | Pass |
| Forged source | A client cannot claim to be City of Eugene GIS. | A request containing `source` returned HTTP 422. | Pass |
| Unsupported report | The API does not say it created a PDF when it only creates HTML. | `format: "pdf"` returned HTTP 422. | Pass |
| Browser security headers | Static responses include CSP, framing, MIME, referrer, and permissions protections. | All configured headers were present. | Pass |
| Large road response | Roads support caching and compression. | Response contained an ETag, cache policy, `Vary`, and gzip encoding. | Pass |
| Chrome refresh after cache fix | A normal refresh loads the current frontend and complete layer responses without requiring a hard refresh. | Chrome loaded the new application bundles; all five layer requests returned HTTP 200, including the compressed roads response. | Pass |
| Shutdown | Normal shutdown removes the temporary service containers without deleting named data volumes. | `docker compose down` completed successfully. | Pass |

Representative commands:

```bash
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:5173/api/health
curl -I http://127.0.0.1:5173/
docker compose down
```

## Recorded browser workflow

The connected browser walkthrough completed during Sprint 4 remains valid for the review workflow retained in Sprint 5:

| Browser check | Observed result | Status |
| --- | --- | --- |
| Load application layers | The browser displayed 13,520 roads and 400 features in each bounded ramp, hydrant, and bicycle collection. | Pass |
| Create annotation | A bike-gap note was saved, selected on the map, and included in the chosen corridor. | Pass |
| Reject annotation | The note remained in history but stopped increasing active concern counts. | Pass |
| Confirm annotation | A confirmed parking conflict remained active and no longer counted as needing review. | Pass |
| Restart backend | Rejected and confirmed statuses remained after a new backend process loaded the store. | Pass |
| Generate report | The downloaded HTML contained readable metrics, signals, notes, and limitations. | Pass |
| Mobile layout | At 390×844, there was no horizontal overflow and the legend remained inside the map. | Pass |
| Product language | The visible interface described a planning tool rather than internal sprint or development terminology. | Pass |

A new automated visual-browser session was unavailable on August 16. The current Sprint 5 service checks above were therefore performed directly against the built containers, and the existing visual evidence is identified separately instead of being presented as a new walkthrough.

## Automated verification

Run the complete final suite from the repository root:

```bash
./scripts/verify_sprint5.sh
```

Final results:

- **45 backend tests passed**.
- **16 frontend tests passed** in 8 test files.
- Python dependency consistency passed.
- Python production dependency audit reported no known vulnerabilities.
- Frontend TypeScript and production build passed.
- Bundle budgets passed for the initial and lazy map chunks.
- npm audit reported no known vulnerabilities.
- **7 of 7 GeoJSON files passed** validation.
- Alembic upgrade, downgrade, and re-upgrade passed.
- Docker Compose configuration passed.
- Backend and frontend container image builds passed.

## What was manual and what was automated

| Behavior | Manual evidence | Automated evidence | Why |
| --- | --- | --- | --- |
| Services assemble correctly | Real Compose startup, proxy, headers, and shutdown. | Compose config and image builds in CI. | Container wiring is easiest to trust when both structural and live checks agree. |
| Annotation create/update | Browser create/reject/confirm and restart workflow. | API, persistence, lifecycle, idempotency, concurrency, and stale-version tests. | A human checks the complete interaction; tests cover many exact failure paths quickly. |
| Invalid input | Live 422 checks for coordinates, source, and report format. | Boundary, extra-field, geometry-size, and lifecycle tests. | Live checks confirm routing and middleware; tests protect all variations. |
| Frontend failure behavior | Visible status and error behavior were checked in the existing browser workflow. | API-client tests verify timeout, unreachable API, malformed payload, and no automatic fallback. | Network failures are repeatable and less ambiguous in automated tests. |
| Report quality | A human read a downloaded report. | Escaping, durable lookup, restart, format, and retention tests. | Readability needs human judgment; security and persistence rules need exact assertions. |
| Layout/accessibility | Mobile layout and keyboard alternatives were reviewed. | Component language and interaction tests. | Visual and assistive behavior cannot be completely proven by unit tests. |

## Failure investigations

### Frontend container could not start with reduced privileges

The first hardened Compose run failed because Nginx attempted to change ownership of `/var/cache/nginx/client_temp` after all Linux capabilities had been removed. Weakening the container was rejected. The image was changed to run directly as the unprivileged `nginx` user, use a non-root main configuration, and mount temporary directories with the correct user ownership. The rebuilt container became healthy, served the frontend, proxied the API, and retained all security restrictions.

### Collinear spatial segments were treated as intersecting

During final review, the segment-intersection helper was found to return true for separate collinear segments. The calculation was revised to require a point to lie on the other segment for collinear contact. A regression test now verifies that separated collinear lines have a positive distance greater than 100 meters in the selected example.

### Earlier false-saved frontend behavior

The audit showed that network failure could trigger browser-memory fallback and still display “saved.” Sprint 5 made mock mode explicit and removed automatic fallback from real requests. Automated API-client tests would now fail if an unreachable API again produced a successful mutation result.

### Chrome refresh could leave the map empty

Chrome revalidated the large roads response and received HTTP 304 with no response body. The frontend loaded all layers with one `Promise.all`, so a failed roads request prevented every successful layer from reaching the map. The roads request now bypasses the browser cache so it always receives a complete payload, and layer results are applied independently with `Promise.allSettled`. A regression test checks the cache setting, while a live Chrome refresh confirmed that the current bundles and every layer response loaded with HTTP 200.

## Final repository checklist

| Question | Answer | Evidence |
| --- | --- | --- |
| Does the README accurately describe the project? | Yes | Start, test, architecture, scope, and risk sections match the final implementation. |
| Can another developer run the project using the README? | Yes | Docker and direct VS Code instructions are provided; live Compose startup passed. |
| Does the documentation match the implementation? | Yes | Required documentation, API contract, data model, operations, audit, and remediation records were reconciled for Sprint 5. |
| Is manual verification documented? | Yes | Current container/API evidence and the retained browser workflow are recorded above. |
| Is AI assistance and engineering judgment documented? | Yes | See `docs/ai-implementation-review.md`. |
| Does Git history show meaningful progress? | Yes | Sprint branches and focused implementation, quality, and documentation commits are preserved. |
| Is Sprint 5 merged into main? | Yes | `sprint-5-final` is preserved and merged into `main`. |
| Is the repository ready to share with an engineer? | Yes | Structure, setup, tests, architecture, risks, and next steps are documented. |

“Ready to share” means professional course-project handoff. It does not override the production launch blockers listed in `docs/production-remediation-status.md`.
