# CURBO Production Readiness Audit

**Audit date:** August 14, 2026<br>
**Reviewed branch:** `sprint-4-milestone`<br>
**Reviewed commit:** `e7021db`<br>
**Working tree note:** `frontend/package-lock.json` contains an uncommitted Nano ID security update from 3.3.16 to 3.3.18.<br>
**Assumption:** CURBO is about to accept paying customers and untrusted network traffic.

## Executive Summary

CURBO is **not production ready** and cannot safely serve paying customers.

The application has no authentication, authorization, tenant isolation, or audit identity. Any caller who can reach the API can read all annotations, create unlimited annotations and reports, and change any review decision. Writes use a process-local list plus a single JSON file. This audit reproduced two independently started application instances generating the same `ann_003` ID and silently deleting the first writer's record.

The frontend silently substitutes browser-only data when the API is unreachable. A failed annotation write can therefore be shown as “saved” even though it disappears on reload. Backend writes mutate memory before disk persistence and have no rollback or idempotency, creating a second data-consistency failure path.

There is no complete production deployment: no production frontend service, TLS ingress, secret manager, security headers, CI/CD, migration pipeline, monitoring, alerting, backups, disaster recovery, or rollback process. The backend health endpoint reports HTTP 200 even when a configured database fails to connect; this was reproduced during the audit.

The browser downloads a 7,786,345-byte roads response containing 13,520 features on every cold load and renders all 13,520 records in a native `<select>`. The backend performs linear scans and approximate rectangle-based spatial calculations. These choices fail well before the requested 10K–1M user range.

The largest business risks are:

1. unauthorized disclosure and manipulation of customer planning data;
2. silent data loss from concurrent writes or browser fallback;
3. denial of service through unbounded annotation geometry and report generation;
4. false planning output derived from approximate geometry and incomplete datasets;
5. undetected outages and unrecoverable data loss due to missing operations systems; and
6. inability to deploy, secure, scale, or roll back the full application consistently.

## Verified Audit Evidence

- 27 backend tests passed with one TestClient dependency warning.
- 13 frontend tests passed.
- The frontend production build passed but emitted a 1,206 KB JavaScript chunk warning.
- The working-tree npm dependency graph reported zero known vulnerabilities after the local Nano ID update.
- The committed lock file at `HEAD` still contains vulnerable `nanoid` 3.3.16; the fix is not committed.
- All seven GeoJSON files passed the repository's structural validator.
- Docker Compose configuration parsed successfully.
- Two simultaneous application instances issued the same annotation ID; the second writer replaced the first writer's data.
- A configured but unreachable database produced `database-unavailable (OperationalError)` while `/api/health` returned HTTP 200 and `status: ok`.
- A 20,000-vertex annotation was accepted with HTTP 201 and produced a 1.2 MB annotation file.
- A client-supplied annotation source of `City of Eugene GIS` was accepted and returned unchanged.
- A request for report format `pdf` returned HTTP 201 but downloaded HTML.
- Report ID `rep_001` was reused after application restart.
- The full roads response was 7,786,345 bytes and took approximately 0.69 seconds to serialize in-process before real network latency.

## Detailed Findings

### PR-01 — All application data and mutations are unauthenticated

**File:** `backend/app/main.py:71-77`; `backend/app/routers/annotations.py`; `backend/app/routers/reports.py`; `backend/app/routers/layers.py`<br>
**Function/Class:** `create_app`; every API route<br>
**Severity:** 🔴 Critical<br>
**Category:** Security — broken access control, authentication, authorization, tenant isolation

**Problem:**<br>
No route requires an authenticated identity, role, organization, or record-level permission. The API has no JWT/session validation, no user model, and no tenant boundary.

**Evidence:**<br>
Routers depend only on `get_store` or settings. `create_app` registers every router without a security dependency. `GET /api/annotations`, `POST /api/annotations`, `PATCH /api/annotations/{id}`, report generation, report download, and all layer reads are public to any network caller.

**Impact:**<br>
Customer annotations and planning decisions can be disclosed, forged, changed, or destroyed. There is no attribution for a review decision and no way to isolate one customer from another.

**Attack Scenario:**<br>
An attacker enumerates annotations, changes confirmed items to rejected, submits misleading observations, generates reports that appear official, or reads another organization's sensitive location notes.

**How To Reproduce:**

```bash
curl http://localhost:8000/api/annotations
curl -X PATCH http://localhost:8000/api/annotations/ann_001 \
  -H 'Content-Type: application/json' -d '{"status":"rejected"}'
```

No credential is required.

**Recommended Fix:**<br>
Put the service behind an identity-aware HTTPS gateway and validate OIDC access tokens in the API. Add users, organizations, roles, record ownership, least-privilege authorization, and append-only audit events. Default every route to denied access.

**Example Fix:**

```python
router = APIRouter(
    prefix="/annotations",
    dependencies=[Depends(require_authenticated_reviewer)],
)
```

This dependency is only a starting point; repository queries must also filter by the authenticated organization and enforce record-level permissions.

### PR-02 — The JSON store loses data under normal concurrency

**File:** `backend/app/services/app_store.py:118-159,186-214,247-269`<br>
**Function/Class:** `AppStore.from_collections`, `next_id`, `create_annotation`, `update_annotation`, `_persist_annotations`<br>
**Severity:** 🔴 Critical<br>
**Category:** Backend architecture — race condition, data corruption, single point of failure

**Problem:**<br>
Every process loads its own copy of annotations and ID counters. Each write replaces the entire shared JSON file without a lock, transaction, revision check, or merge. The fixed `.tmp` name also creates a collision between concurrent writers.

**Evidence:**<br>
The audit started two application instances against the same file. Both issued `ann_003`. The second write replaced the first. A new application contained only the second writer's record.

**Impact:**<br>
Valid customer work disappears without an error. Multiple Uvicorn workers, multiple containers, rolling deployments, or overlapping requests make persistence unsafe. Horizontal scaling is impossible.

**Attack Scenario:**<br>
An attacker or ordinary burst of users sends overlapping creates/updates. Last writer wins with stale process state, deleting unrelated records.

**How To Reproduce:**<br>
Start two application instances with the same `ANNOTATION_FILE`, create one annotation through each, then restart and list annotations. Both instances generate the same ID and one record is absent.

**Recommended Fix:**<br>
Replace `AppStore` writes with transactional PostgreSQL persistence. Use UUID/ULID identifiers, unique constraints, optimistic version columns, row-level authorization filters, and explicit transaction boundaries. Do not run more than one worker until migration is complete.

**Example Fix:**

```sql
UPDATE annotations
SET status = :status, version = version + 1, updated_at = now()
WHERE id = :id AND organization_id = :org AND version = :expected_version;
```

Treat zero updated rows as a conflict or missing/unauthorized record.

### PR-03 — Network failures create false “saved” states and data loss

**File:** `frontend/src/api/client.ts:28-55`; `frontend/src/api/annotations.ts:20-53`; `frontend/src/api/fallbackData.ts:279-309`; `frontend/src/App.tsx:265-329`<br>
**Function/Class:** `fetchJsonWithFallback`, `createAnnotation`, `updateAnnotationStatus`, `handleCreateAnnotation`<br>
**Severity:** 🔴 Critical<br>
**Category:** Reliability — silent data loss, misleading UX

**Problem:**<br>
The same automatic fallback used for reads is used for POST and PATCH. A network `TypeError` runs a browser-memory mutation. `App.tsx` then announces that the annotation or status was saved.

**Evidence:**<br>
`fetchJsonWithFallback` catches network failure and invokes the fallback regardless of HTTP method. `addFallbackAnnotation` changes only a module-level variable. `App.tsx` displays “New annotation saved” and “Annotation status saved.”

**Impact:**<br>
Paying users believe work is durable when it is not. Reloading the page loses it. Status changes for records loaded from the server may fail because those records do not exist in fallback memory.

**Attack Scenario:**<br>
An intermittent network, blocked API, malicious proxy, or backend outage causes users to continue entering data that is never stored.

**How To Reproduce:**<br>
Load the application, stop the backend, create an annotation, observe the success message, then reload the page.

**Recommended Fix:**<br>
Never automatically fall back for mutations. Either block writes offline or implement a durable browser outbox with explicit `unsynced`, `syncing`, `conflict`, and `saved` states. A server acknowledgement must be required before “saved” is displayed.

**Example Fix:**

```ts
export function createAnnotation(draft: AnnotationDraft) {
  return fetchJson("/api/annotations", {
    method: "POST",
    body: JSON.stringify(draft)
  }); // no fallback
}
```

### PR-04 — Unbounded public writes permit memory, CPU, and disk exhaustion

**File:** `backend/app/schemas/geojson.py:34-46`; `backend/app/main.py:63-69`; `backend/app/routers/reports.py:15-58`; `backend/app/services/app_store.py:186-205`<br>
**Function/Class:** `LineStringGeometry`, `create_corridor_report`, `_persist_annotations`<br>
**Severity:** 🔴 Critical<br>
**Category:** Security — denial of service, API abuse, cost amplification

**Problem:**<br>
LineString coordinates have no maximum vertex count. The API has no request-body limit, rate limit, per-user quota, report quota, or storage quota. Each annotation rewrites the entire annotation file; each report writes another file.

**Evidence:**<br>
The audit submitted 20,000 positions. The API returned HTTP 201 and wrote a 1.2 MB JSON file. No authentication was required. Repeated report POSTs create files synchronously.

**Impact:**<br>
An attacker can exhaust memory, worker threads, CPU, disk, and network bandwidth. Increasing annotation history makes every later write progressively more expensive.

**Attack Scenario:**<br>
A bot submits many maximum-description annotations with hundreds of thousands of vertices and continuously generates reports until the service or host volume fails.

**How To Reproduce:**<br>
POST a LineString with tens of thousands of valid coordinate pairs, then repeat the request or report generation while watching process memory and disk use.

**Recommended Fix:**<br>
Enforce request size at the edge, cap geometry vertices and total geometry length, rate-limit by identity and organization, add quotas, move reports to controlled background jobs, and monitor storage.

**Example Fix:**

```python
class LineStringGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]] = Field(min_length=2, max_length=1_000)
```

Also enforce a smaller body limit at the reverse proxy; application validation alone still requires parsing the body.

### PR-05 — Failed persistence leaves memory changed and retries create duplicates

**File:** `backend/app/services/app_store.py:247-269`; `backend/app/routers/annotations.py:20-59`<br>
**Function/Class:** `create_annotation`, `update_annotation`<br>
**Severity:** 🔴 Critical<br>
**Category:** Reliability — non-transactional writes, inconsistency, idempotency

**Problem:**<br>
Create appends to memory and update mutates status before disk persistence. If writing fails, FastAPI returns an error but process memory remains changed. POST has no idempotency key, so a client retry creates another record.

**Evidence:**<br>
`self.annotations.append(annotation)` and `annotation["status"] = status` occur before `_persist_annotations()`. There is no exception rollback. IDs increment before persistence.

**Impact:**<br>
Different clients can observe conflicting state, a restart can revert an apparently visible record, and retrying after a timeout can duplicate customer work.

**Attack Scenario:**<br>
An attacker fills the volume or changes file permissions. Subsequent writes return failures while memory diverges from disk, causing unpredictable reads and duplicate retries.

**How To Reproduce:**<br>
Make the annotation directory unwritable, submit a create/update, observe HTTP 500, then list annotations from the still-running process and after restart.

**Recommended Fix:**<br>
Use database transactions and idempotency keys. Until migration, persist a copied candidate state first and replace in-memory state only after a successful durable write; this still does not solve multi-process races.

**Example Fix:**

```python
candidate = [*self.annotations, annotation]
self._persist(candidate)
self.annotations = candidate
```

### PR-06 — Demo records silently contaminate real customer data

**File:** `backend/app/services/app_store.py:57-93,161-184`; `frontend/src/api/fallbackData.ts:165-188`<br>
**Function/Class:** `_default_annotations`, `_load_annotations`<br>
**Severity:** 🟠 Major<br>
**Category:** Data integrity — synthetic production data

**Problem:**<br>
When the annotation file is missing, the backend inserts two sample annotations that look like planner records. The first real write persists those samples. There is no explicit demo-mode flag.

**Evidence:**<br>
`_load_annotations` returns `_default_annotations()` for a missing file. The records use `source: planner` and realistic descriptions rather than unmistakable fixture metadata.

**Impact:**<br>
Customer counts, review priorities, and reports can include fake observations. This undermines trust and can influence planning decisions.

**Attack Scenario:**<br>
An operational restore or new tenant starts with a missing file; synthetic observations are treated as real and included in reports.

**How To Reproduce:**<br>
Start with a new `ANNOTATION_FILE`, call `GET /api/annotations`, and observe `ann_001` and `ann_002` before any user write.

**Recommended Fix:**<br>
Default production storage to empty. Move sample records to a dedicated seed command gated by `DEMO_DATA=true`, with obvious fixture ownership and separate storage.

**Example Fix:**

```python
if annotation_file is None or not annotation_file.exists():
    return []
```

### PR-07 — Clients can forge authoritative-looking annotation sources

**File:** `backend/app/schemas/annotations.py:34-47`; `backend/app/routers/annotations.py:20-42`<br>
**Function/Class:** `AnnotationCreate`, `create_annotation`<br>
**Severity:** 🟠 Major<br>
**Category:** Security — integrity, impersonation

**Problem:**<br>
The caller controls the persisted `source` field. There is no identity system or server-side provenance rule.

**Evidence:**<br>
The audit submitted `source: City of Eugene GIS`; the API accepted and returned it. The frontend displays source information in feature details.

**Impact:**<br>
Malicious observations can appear to come from an authoritative agency, reviewer, or import. Reports and screenshots can mislead customers or the public.

**Attack Scenario:**<br>
An attacker creates a false safety concern labeled as an official City source and distributes the generated report.

**How To Reproduce:**<br>
POST an annotation with a chosen `source` string and inspect the returned feature.

**Recommended Fix:**<br>
Remove `source` from public create input. Derive creator, organization, import source, and provenance from the authenticated principal or a privileged import pipeline.

**Example Fix:**

```python
source = f"user:{principal.user_id}"
```

### PR-08 — Compose exposes PostgreSQL with default credentials

**File:** `docker-compose.yml:2-18`; `.env.example:1-6`; `backend/app/config.py:27-31`<br>
**Function/Class:** `postgres` service; `Settings`<br>
**Severity:** 🔴 Critical<br>
**Category:** Security/Infrastructure — secrets, database exposure

**Problem:**<br>
PostgreSQL is published on host port 5432 and defaults to `curbo_user` / `curbo_password`. Credentials are documented and optional rather than mandatory secrets.

**Evidence:**<br>
Compose uses `${POSTGRES_PASSWORD:-curbo_password}` and `ports: 5432:5432`.

**Impact:**<br>
If this configuration is used on a shared or internet-reachable host, the database can be compromised with known credentials. Future customer data would be exposed or destroyed.

**Attack Scenario:**<br>
An attacker scans port 5432 and authenticates using repository-default credentials.

**How To Reproduce:**<br>
Start the database profile without overriding variables and connect with the documented username/password.

**Recommended Fix:**<br>
Remove the host port in production, place PostgreSQL on a private network, require secret injection, rotate credentials, enforce TLS, and restrict database security groups.

**Example Fix:**

```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
# no host ports in production
```

### PR-09 — There is no secure production web boundary

**File:** `docker-compose.yml:20-40`; `backend/Dockerfile`; `frontend/vite.config.ts`<br>
**Function/Class:** backend and commented frontend services<br>
**Severity:** 🔴 Critical<br>
**Category:** DevOps/Security — deployment, TLS, reverse proxy, security headers

**Problem:**<br>
Only the backend has a runnable container. The frontend service is commented out and has no Dockerfile or production static host. There is no TLS termination, reverse proxy, WAF, security-header policy, hostname configuration, or trusted deployment manifest.

**Evidence:**<br>
Compose publishes Uvicorn directly. Vite configuration is a development server. No Nginx, Kubernetes, cloud deployment, or hosting configuration exists.

**Impact:**<br>
The full product cannot be deployed consistently. Direct HTTP exposes traffic to interception and removes the edge controls needed for body limits, rate limits, headers, and safe routing.

**Attack Scenario:**<br>
Credentials added later are transmitted through a direct or incorrectly configured HTTP endpoint; attackers alter or observe sessions and API traffic.

**How To Reproduce:**<br>
Run the documented Compose configuration and inspect exposed services; only port 8000 is served and no HTTPS listener exists.

**Recommended Fix:**<br>
Build immutable frontend and backend artifacts, deploy behind managed HTTPS ingress, enforce HSTS/CSP/frame protections/content sniffing/referrer policy, terminate TLS with managed certificates, and separate internal from public networks.

**Example Fix:**<br>
Architectural change required; a local code snippet is not a safe substitute for an owned production platform.

### PR-10 — Health checks declare success during dependency failure

**File:** `backend/app/db.py:26-46`; `backend/app/main.py:30-50`; `backend/app/routers/health.py:6-17`<br>
**Function/Class:** `initialize_database`, lifespan, `get_health`<br>
**Severity:** 🟠 Major<br>
**Category:** Reliability/Observability — false readiness

**Problem:**<br>
Database initialization catches every exception and allows startup. The only health route always returns `status: ok` and does not test database, data cache, annotation writeability, or report storage.

**Evidence:**<br>
The audit configured an unreachable PostgreSQL endpoint. Application state reported `database-unavailable (OperationalError)`, while `/api/health` returned HTTP 200 and `status: ok`.

**Impact:**<br>
Load balancers send traffic to broken instances. Deployments appear successful while dependencies are unavailable. Alerts cannot distinguish liveness from readiness.

**Attack Scenario:**<br>
Not required; a database outage or full volume creates the false-positive condition.

**How To Reproduce:**<br>
Set `DATABASE_URL` to an unreachable host, start the API, and request `/api/health`.

**Recommended Fix:**<br>
Keep a minimal liveness endpoint, add a readiness endpoint that verifies required dependencies and writable storage, log startup failures, and fail closed when a configured required dependency is unavailable.

**Example Fix:**

```python
@router.get("/ready")
def ready(request: Request):
    if request.app.state.db_status != "connected":
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}
```

### PR-11 — The advertised database path is disconnected from runtime data

**File:** `backend/app/db.py`; `backend/app/main.py:33-50`; `backend/app/dependencies.py`; `backend/app/services/app_store.py`<br>
**Function/Class:** `initialize_database`, `get_store`, `AppStore`<br>
**Severity:** 🟠 Major<br>
**Category:** Backend/Database architecture — incomplete implementation

**Problem:**<br>
Configuring `DATABASE_URL` creates tables, but every live route continues to use the in-memory/JSON store. The session factory is placed on app state and never consumed.

**Evidence:**<br>
No router or service obtains a database session. There is no ingestion or repository layer. `POSTGRES_*` settings do not construct a database URL.

**Impact:**<br>
Operators can believe persistence is database-backed when it is not. Database backups do not protect annotations. The service cannot scale despite a “connected” database status.

**Attack Scenario:**<br>
Not required; deployment misconfiguration creates a false durability assumption.

**How To Reproduce:**<br>
Enable `DATABASE_URL`, create an annotation, and query the SQLAlchemy annotations table; the route still writes the JSON file.

**Recommended Fix:**<br>
Either remove/feature-flag the unused database facade or complete transactional repositories and data migration before presenting the database as supported.

**Example Fix:**<br>
Architectural change required: route → domain service → database repository, with no fallback to JSON in production.

### PR-12 — Database models lack production integrity and spatial design

**File:** `backend/app/models/*.py`; `backend/app/db.py:40-44`<br>
**Function/Class:** `Annotation`, `CorridorReport`, `Road`, `CurbRamp`, `Hydrant`; `Base.metadata.create_all`<br>
**Severity:** 🟠 Major<br>
**Category:** Database — migrations, constraints, indexes, normalization

**Problem:**<br>
Geometry is generic JSON rather than PostGIS geometry. Models lack organization/user foreign keys, status/type check constraints, uniqueness beyond IDs, update/version fields, audit events, deletion policy, spatial indexes, and relationships. Bicycle facilities have no model. `create_all` replaces versioned migrations.

**Evidence:**<br>
The models define minimal columns only. There is no Alembic configuration or migration directory.

**Impact:**<br>
The schema cannot enforce tenant isolation or domain integrity and cannot execute indexed spatial queries. Schema changes have no reviewable upgrade or rollback path.

**Attack Scenario:**<br>
Compromised or buggy application code writes cross-tenant, invalid-status, or malformed geometry rows because the database has no defensive constraints.

**How To Reproduce:**<br>
Inspect generated DDL after `create_all`; no spatial types, foreign keys, or domain checks exist.

**Recommended Fix:**<br>
Design normalized tenant-aware tables, use PostGIS geometry with SRID constraints and GiST indexes, add audit/version columns, foreign keys and checks, and manage changes with Alembic migration/rollback tests.

**Example Fix:**

```sql
ALTER TABLE annotations
  ADD CONSTRAINT annotation_status_check
  CHECK (status IN ('pending','reviewed','confirmed','rejected'));
CREATE INDEX annotations_geometry_gist ON annotations USING gist (geometry);
```

### PR-13 — Report files are not durable, unique, authorized, or bounded

**File:** `backend/app/routers/reports.py:15-72`; `backend/app/schemas/reports.py:6-16`; `backend/app/services/app_store.py:277-290`<br>
**Function/Class:** `create_corridor_report`, `download_report`, `CorridorReportRequest`, report counter<br>
**Severity:** 🟠 Major<br>
**Category:** Reliability/Security — artifact lifecycle, storage abuse

**Problem:**<br>
Report metadata exists only in memory. IDs reset after restart, old links return 404, and new reports reuse old filenames. Any format string is accepted but HTML is always generated. No ownership, retention, quota, cleanup, or file-existence check exists.

**Evidence:**<br>
The audit requested `format: pdf`; the API returned 201 and served `text/html`. After restart, the next report was again `rep_001`, overwriting the persistent-volume path.

**Impact:**<br>
Customers lose report links, artifacts are overwritten, storage grows without control, and the API lies about requested formats.

**Attack Scenario:**<br>
An unauthenticated bot generates reports continuously to consume disk; a restart then reuses IDs and replaces prior customer artifacts.

**How To Reproduce:**<br>
Generate a report, restart, generate another, and compare IDs. Submit `format: pdf` and inspect the response content type.

**Recommended Fix:**<br>
Persist report metadata with tenant ownership, use UUIDs, validate a literal format, place artifacts in object storage with retention, authorize downloads, and add quotas/background jobs.

**Example Fix:**

```python
class CorridorReportRequest(BaseModel):
    road_id: str
    format: Literal["html"] = "html"
```

### PR-14 — Every cold page load transfers and validates the full road network

**File:** `frontend/src/App.tsx:92-123`; `frontend/src/api/layers.ts`; `backend/app/routers/layers.py`; `backend/app/schemas/layers.py`<br>
**Function/Class:** `loadData`, `getRoads`, `get_roads`<br>
**Severity:** 🟠 Major<br>
**Category:** Scalability/Cost — bandwidth, CPU, latency

**Problem:**<br>
The frontend requests every road without a bounding box, pagination, tiles, compression policy, cache validator, or CDN. FastAPI response models validate and serialize the collection for each request.

**Evidence:**<br>
The observed roads response was 7,786,345 bytes for 13,520 features and took approximately 0.69 seconds in-process. No cache-control or ETag implementation exists.

**Impact:**<br>
Cold-start latency and egress costs rise linearly with users. A modest traffic burst consumes backend CPU and bandwidth. Mobile users receive unnecessary data.

**Attack Scenario:**<br>
Repeated unauthenticated GETs force expensive serialization and bandwidth consumption.

**How To Reproduce:**<br>
Measure `GET /api/layers/roads` response size and repeat it concurrently.

**Recommended Fix:**<br>
Use versioned vector tiles or viewport-based endpoints, CDN caching, gzip/Brotli, ETags, immutable dataset versions, and server-side search.

**Example Fix:**<br>
Require `bbox` for large layers and return only the current viewport as an interim control; do not treat this as a replacement for vector tiles at scale.

### PR-15 — Frontend rendering reparses large map data and builds 13,520 DOM options

**File:** `frontend/src/components/MapView.tsx:174-193`; `frontend/src/components/CorridorSelector.tsx:24-36`<br>
**Function/Class:** Map source synchronization effect; `CorridorSelector`<br>
**Severity:** 🟠 Major<br>
**Category:** Frontend performance — rendering, memory, UX

**Problem:**<br>
Any change to any layer causes `setData` to run for all five MapLibre sources, including the full roads collection. The corridor selector maps all 13,520 road segments into native options with duplicates and no search or virtualization.

**Evidence:**<br>
The effect has all collections in one dependency list and sets every source. `CorridorSelector` directly maps the entire roads array.

**Impact:**<br>
Annotation updates can trigger unnecessary road reparsing. The selector is slow and unusable, especially on low-memory/mobile devices. Long tasks and browser crashes become likely as data grows.

**Attack Scenario:**<br>
No attacker is required; normal annotation editing repeatedly updates a heavy map source.

**How To Reproduce:**<br>
Profile an annotation change with browser performance tools and inspect MapLibre source updates and the 13,520-option DOM.

**Recommended Fix:**<br>
Split source-update effects by collection, replace the selector with debounced server search and a virtualized result list, group road segments into real corridors, and lazy-load the map.

**Example Fix:**

```ts
useEffect(() => {
  setSourceData(mapRef.current!, SOURCE_IDS.annotations, annotations);
}, [annotations]);
```

### PR-16 — Spatial analysis is both inaccurate and O(n)

**File:** `backend/app/services/app_store.py:216-220`; `backend/app/services/spatial_queries.py:172-207,273-336`<br>
**Function/Class:** `get_road_feature`, `_expanded_bbox`, `_count_near_features`, `analyze_corridor`<br>
**Severity:** 🟠 Major<br>
**Category:** Backend/Database — correctness and query performance

**Problem:**<br>
Road lookup and feature proximity are linear scans. Proximity uses one axis-aligned rectangle around the entire road geometry rather than distance to the road. Multipart/diagonal/curved roads can include distant assets.

**Evidence:**<br>
The code documents the rectangle limitation and filters every feature collection for every analysis.

**Impact:**<br>
Results produce false positives/negatives and latency grows with every dataset and annotation. The service cannot use database indexes or scale horizontally safely.

**Attack Scenario:**<br>
Repeated analysis requests consume CPU. More importantly, customers may act on incorrect corridor counts.

**How To Reproduce:**<br>
Create a diagonal road and place an asset inside its bounding rectangle but far from the line; it is counted as nearby.

**Recommended Fix:**<br>
Store authoritative geometry in PostGIS with a projected SRID, GiST indexes, and `ST_DWithin`/buffer queries. Define whether a “corridor” is one segment, a named street, or a selected chain.

**Example Fix:**

```sql
SELECT count(*) FROM curb_ramps
WHERE ST_DWithin(curb_ramps.geometry::geography, :road_geography, :meters);
```

### PR-17 — Decision labels are derived from incomplete, unvalidated evidence

**File:** `backend/app/services/spatial_queries.py:219-270,334-342`; `data/eugene/README.md:12`; `frontend/src/components/ReportPanel.tsx`<br>
**Function/Class:** `_build_review_assessment`, `analyze_corridor`, `ReportPanel`<br>
**Severity:** 🟠 Major<br>
**Category:** Product/Data risk — incorrect decisions, legal/customer complaints

**Problem:**<br>
The UI presents Low/Medium/High review attention and “bicycle feasibility” from a hand-coded heuristic. Roads are a dated snapshot; ramps, hydrants, and bicycle facilities are only 400-feature extracts. Crash, speed, volume, exposure, parking, right-of-way, and transit data are absent.

**Evidence:**<br>
The score starts at 4 and applies fixed weights. The data README explicitly states three layers are demonstration extracts.

**Impact:**<br>
Customers can interpret incomplete or false counts as planning evidence. Disclaimers do not prevent screenshots, exported reports, procurement claims, or downstream misuse.

**Attack Scenario:**<br>
Malicious or biased annotations manipulate the heuristic because unauthenticated reviewer notes directly affect attention labels.

**How To Reproduce:**<br>
Add two bike-gap annotations near a road and observe review attention rise without any authoritative validation.

**Recommended Fix:**<br>
Remove “feasibility” and priority-like labels from production until data governance, validation, methodology ownership, calibration, and human approval exist. Show dataset coverage/freshness next to every result and version all inputs/methods in reports.

**Example Fix:**<br>
Return raw, sourced observations and coverage metadata instead of a priority label until an approved decision model exists.

### PR-18 — Read fallback hides outages and displays fabricated evidence as loaded

**File:** `frontend/src/api/client.ts:28-55`; `frontend/src/api/fallbackData.ts:27-237`; `frontend/src/App.tsx:92-118`<br>
**Function/Class:** `fetchJsonWithFallback`, fallback constants, `loadData`<br>
**Severity:** 🟠 Major<br>
**Category:** Reliability/Data integrity — degraded-mode deception

**Problem:**<br>
Network failures return synthetic datasets and invented corridor counts. Because fallback resolves successfully, `App.tsx` announces that Eugene infrastructure layers loaded. Degraded state is only logged to the developer console.

**Evidence:**<br>
Fallback summaries contain fixed counts not derived from the fallback collections. The success message is unconditional after all fallback promises resolve.

**Impact:**<br>
Customers cannot distinguish authoritative, cached, partial, synthetic, and unavailable information. Reports or decisions can be based on demo data.

**Attack Scenario:**<br>
A proxy blocks the API or DNS fails. Users continue operating on synthetic evidence without a visible warning.

**How To Reproduce:**<br>
Stop the backend, open the frontend, and observe a populated map and successful loaded message.

**Recommended Fix:**<br>
Make source mode part of every API result and application state. Display a blocking degraded/demo banner. Do not provide fabricated analysis in a production build. Fail closed for decision workflows.

**Example Fix:**

```ts
type DataMode = "live" | "stale-cache" | "demo" | "unavailable";
```

Require the UI to render and acknowledge this mode explicitly.

### PR-19 — The data refresh pipeline can publish bad data while reporting success

**File:** `scripts/fetch_eugene_data.py:46-95,98-152`; `scripts/validate_geojson.py`<br>
**Function/Class:** `fetch_geojson`, `normalize`, `main`<br>
**Severity:** 🟠 Major<br>
**Category:** Data pipeline — validation, atomic publishing, operational signaling

**Problem:**<br>
Refresh performs minimal structural checks, silently drops malformed features, does not run the repository validator before replacement, has no expected count/extent/schema checks, and returns exit code 0 even when fetches fail.

**Evidence:**<br>
Failures increment a counter and print a warning, but `main()` always returns 0. A normalized collection is written and replaced immediately.

**Impact:**<br>
Scheduled jobs can appear successful while data is stale, empty, truncated, or schema-drifted. Bad datasets can be committed or deployed without an alert.

**Attack Scenario:**<br>
Compromised or malformed upstream data passes weak checks and becomes customer-visible. Operator-controlled URL overrides can also fetch from unintended sources in a compromised CI environment.

**How To Reproduce:**<br>
Set an invalid Eugene URL, run the script, and inspect the zero exit status despite the failure message.

**Recommended Fix:**<br>
Fetch into a versioned staging directory, validate geometry/schema/count/extent/uniqueness/checksum, compare against anomaly thresholds, publish atomically only after approval, and return nonzero on failed refresh in strict/CI mode.

**Example Fix:**

```python
return 1 if failures else 0
```

This is only the signaling fix; staged validation and provenance are still required.

### PR-20 — Frontend requests can hang indefinitely and trust malformed responses

**File:** `frontend/src/api/client.ts:24-62`; `frontend/src/App.tsx:125-160`<br>
**Function/Class:** `fetchJsonWithFallback`, `refreshCorridor`<br>
**Severity:** 🟠 Major<br>
**Category:** Frontend reliability — timeout, cancellation, contract validation

**Problem:**<br>
Fetch calls have no timeout or `AbortController`. Request IDs ignore stale responses but do not cancel network/CPU work. Parsed JSON is cast to TypeScript types without runtime validation.

**Evidence:**<br>
`fetch(apiUrl(path), init)` uses caller options only; no signal/timeout exists. The result is `as T`.

**Impact:**<br>
Slow connections leave loading states indefinitely, waste backend work, and can crash rendering when a response shape drifts.

**Attack Scenario:**<br>
A slow or malicious upstream holds connections open or returns structurally valid JSON with unexpected fields/types.

**How To Reproduce:**<br>
Proxy the API and never complete a response; the frontend has no request deadline.

**Recommended Fix:**<br>
Add timeouts and cancellation, centralized retry policy for safe idempotent reads only, runtime response schemas, and generated OpenAPI clients/contracts.

**Example Fix:**

```ts
const signal = AbortSignal.timeout(10_000);
const response = await fetch(url, { ...init, signal });
```

### PR-21 — Critical map workflows are not keyboard-accessible

**File:** `frontend/src/components/MapView.tsx`; `frontend/src/components/AnnotationTool.tsx`; `frontend/src/components/FeaturePopup.tsx`<br>
**Function/Class:** map click drawing and feature interaction<br>
**Severity:** 🟠 Major<br>
**Category:** Frontend — accessibility, legal/compliance risk

**Problem:**<br>
Point/line drawing and direct feature inspection depend on pointer interactions with a WebGL canvas. Manual coordinates cover point placement only. There is no keyboard-equivalent line workflow, accessible map feature list, automated axe suite, or documented WCAG conformance.

**Evidence:**<br>
Map interactions are wired to click/mouseenter/mouseleave events. The automated frontend suite does not include accessibility tooling or keyboard end-to-end journeys.

**Impact:**<br>
Keyboard-only and assistive-technology users cannot complete core tasks. A civic product risks accessibility complaints and contractual/legal noncompliance.

**Attack Scenario:**<br>
Not applicable; normal users are blocked.

**How To Reproduce:**<br>
Attempt to draw and finish a line using only the keyboard and a screen reader.

**Recommended Fix:**<br>
Provide accessible feature search/list alternatives, keyboard coordinate editing for lines, focus management, descriptive map summaries, axe checks, and manual WCAG 2.2 AA review.

**Example Fix:**<br>
Add an editable coordinate table with add/remove/reorder controls so every drawn geometry can be created without the canvas.

### PR-22 — Frontend bundle size has no budget or code splitting

**File:** `frontend/src/App.tsx`; `frontend/src/components/MapView.tsx`; `frontend/vite.config.ts`<br>
**Function/Class:** static MapLibre import and single application bundle<br>
**Severity:** 🟠 Major<br>
**Category:** Frontend performance/Cost

**Problem:**<br>
MapLibre is included in the initial bundle. No lazy routes/components, code-splitting policy, performance budget, or bundle regression test exists.

**Evidence:**<br>
The production build emitted a 1,206.14 KB minified JavaScript chunk warning (329.66 KB gzip).

**Impact:**<br>
Slow first load, higher bandwidth cost, poor mobile experience, and unbounded future bundle growth.

**Attack Scenario:**<br>
Not required; normal traffic incurs the cost.

**How To Reproduce:**<br>
Run `npm run build` and inspect the chunk warning.

**Recommended Fix:**<br>
Lazy-load MapLibre/map UI, configure deterministic chunking, set CI size budgets, and measure real-device Core Web Vitals.

**Example Fix:**

```ts
const MapView = lazy(() => import("./components/MapView"));
```

### PR-23 — Dependency management is not reproducible or fully secured

**File:** `backend/requirements.txt`; `frontend/package-lock.json`; `backend/Dockerfile:5-6`<br>
**Function/Class:** dependency installation<br>
**Severity:** 🟠 Major<br>
**Category:** Supply chain — version drift, vulnerability management

**Problem:**<br>
Python dependencies use broad ranges without hashes or a lock/constraints file. Test and production packages share one requirements file. The container installs whatever versions resolve at build time. The committed frontend lock still contains high-advisory `nanoid` 3.3.16; only the working tree updates it to 3.3.18.

**Evidence:**<br>
Backend tests emitted a TestClient dependency warning. `requirements.txt` permits large future version drift. `git diff` shows the Nano ID fix is uncommitted.

**Impact:**<br>
Two builds from the same commit can differ, new upstream releases can break production, and the remote branch remains vulnerable despite a clean local audit.

**Attack Scenario:**<br>
A compromised or newly vulnerable transitive dependency is resolved during a rebuild; no lock or hash prevents it.

**How To Reproduce:**<br>
Compare dependency resolution dates or inspect `HEAD:frontend/package-lock.json` for Nano ID 3.3.16.

**Recommended Fix:**<br>
Commit the frontend lock update after tests, use a reviewed Python lock with hashes, split runtime/dev dependencies, add Python and container vulnerability scanning, and automate dependency updates through reviewed PRs.

**Example Fix:**<br>
Generate a pinned constraints/lock file in CI and install with hash verification rather than open ranges.

### PR-24 — The backend container is not hardened

**File:** `backend/Dockerfile`; repository root (missing `.dockerignore`); `docker-compose.yml:20-33`<br>
**Function/Class:** backend image and service<br>
**Severity:** 🟠 Major<br>
**Category:** Infrastructure/Security — container isolation, build context

**Problem:**<br>
The image runs as root, uses an unpinned base tag, installs unpinned dependencies and test tooling, has no image healthcheck, and has no read-only filesystem/capability/resource policy. There is no `.dockerignore`, so local `.env`, `.git`, node modules, virtual environments, and hundreds of megabytes of unrelated files can be sent to a local or remote builder.

**Evidence:**<br>
The Dockerfile contains no `USER` directive or hardening. The current workspace is approximately 435 MB while application source is small.

**Impact:**<br>
Container compromise has unnecessary privileges, builds are slow and leak local context to builders, and resource exhaustion can affect the host.

**Attack Scenario:**<br>
A runtime vulnerability gives code execution as root inside the container; a remote build service receives secrets present in the build context.

**How To Reproduce:**<br>
Inspect the built image user and Docker build context size.

**Recommended Fix:**<br>
Add `.dockerignore`, pin the base digest, create a non-root user, split build/runtime dependencies, add healthcheck/resource limits/security options, and scan/sign images.

**Example Fix:**

```dockerfile
RUN addgroup --system curbo && adduser --system --ingroup curbo curbo
USER curbo
```

### PR-25 — No CI/CD, environment promotion, or rollback system exists

**File:** repository root (missing `.github/workflows` or equivalent); `scripts/verify_sprint4.sh`<br>
**Function/Class:** release process<br>
**Severity:** 🔴 Critical<br>
**Category:** DevOps — CI/CD, deployment safety, rollback

**Problem:**<br>
Checks run only when a person executes a shell script. There is no protected pull-request gate, artifact build/signing, deployment pipeline, staging promotion, migration gate, canary/blue-green strategy, or rollback automation. The verifier silently skips Docker when unavailable and still prints “passed.”

**Evidence:**<br>
No CI configuration exists. `verify_sprint4.sh` treats missing Docker as a skip and always prints the final success line if other commands pass.

**Impact:**<br>
Broken or vulnerable code can reach production. Builds are not reproducible, provenance is absent, and recovery depends on manual actions during incidents.

**Attack Scenario:**<br>
A malicious or accidental change bypasses local verification and is deployed without review or signed artifacts.

**How To Reproduce:**<br>
Inspect the repository for CI/deployment manifests; none exist.

**Recommended Fix:**<br>
Add mandatory CI for tests, lint, type check, audits, SAST, secret scan, data validation, container build/scan, and deployment smoke tests. Produce immutable signed artifacts and implement staged promotion and one-command rollback.

**Example Fix:**<br>
Start with a protected workflow that runs `verify_sprint4.sh` plus Python audit, lint/type checks, and a real container startup test; do not allow skipped required checks.

### PR-26 — Incidents and abuse are invisible

**File:** entire backend/frontend; `backend/app/routers/health.py`; `frontend/src/api/client.ts:54`; `frontend/src/components/MapView.tsx:141-145`<br>
**Function/Class:** logging, metrics, tracing, audit<br>
**Severity:** 🔴 Critical<br>
**Category:** Observability/Security — logging, monitoring, alerting

**Problem:**<br>
There are no structured application logs, request/correlation IDs, metrics, traces, exception tracking, audit events, dashboards, alerts, SLOs, or abuse monitoring. Frontend failures are console warnings. Database failure is stored as a string and not surfaced.

**Evidence:**<br>
Only default Uvicorn access/error output and browser `console.warn` calls exist. No observability dependency or configuration is present.

**Impact:**<br>
Data loss, unauthorized changes, outages, slow requests, disk exhaustion, and attack traffic can continue undetected. Incident investigation cannot identify who changed what.

**Attack Scenario:**<br>
An attacker modifies annotations or fills report storage. There is no identity, audit event, alert, or rate metric to reveal the activity.

**How To Reproduce:**<br>
Change an annotation and inspect available records; no actor/IP/correlation/audit history is stored.

**Recommended Fix:**<br>
Add structured JSON logs with redaction, request IDs, metrics, traces, error reporting, security/audit events, dashboards, alerts, and explicit SLOs. Separate immutable audit logs from debug logs.

**Example Fix:**<br>
Emit an audit event containing actor, organization, action, target, old/new status, timestamp, request ID, and outcome after the transaction commits.

### PR-27 — No backup, restore, retention, or disaster-recovery process exists

**File:** `docker-compose.yml:31-45`; documentation; `backend/app/services/app_store.py`<br>
**Function/Class:** annotation/report/PostgreSQL volumes<br>
**Severity:** 🔴 Critical<br>
**Category:** Reliability — backup, disaster recovery, retention

**Problem:**<br>
Named volumes are the only durability mechanism. There are no scheduled backups, offsite copies, restore tests, retention policy, recovery point/time objectives, corruption repair tooling, or regional recovery plan.

**Evidence:**<br>
Compose declares volumes only. Documentation tells users a corrupt JSON file must be restored or removed but provides no restore source or procedure.

**Impact:**<br>
Host loss, volume deletion, corruption, ransomware, or operator error permanently destroys customer records and reports.

**Attack Scenario:**<br>
An attacker or operator deletes the Docker volumes; there is no recoverable copy.

**How To Reproduce:**<br>
No safe production reproduction is appropriate; inspect the repository for backup and restore jobs/runbooks—none exist.

**Recommended Fix:**<br>
Use managed PostgreSQL point-in-time recovery and versioned object storage, encrypted backups, cross-account/region copies where required, defined RPO/RTO, and automated restore drills.

**Example Fix:**<br>
Architectural/operational implementation required; a backup is not complete until a restore test succeeds.

### PR-28 — Test coverage excludes the production failure modes

**File:** `backend/tests`; `frontend/src/**/*.test.*`; `scripts/verify_sprint4.sh`<br>
**Function/Class:** automated test strategy<br>
**Severity:** 🟠 Major<br>
**Category:** QA/Reliability — coverage gaps

**Problem:**<br>
There are no concurrency, multi-worker, load, authentication, authorization, tenant isolation, rate-limit, security-header, backup/restore, migration, PostGIS, production Docker runtime, browser end-to-end, outage/recovery, accessibility, or chaos tests. There is no coverage threshold.

**Evidence:**<br>
The suite has 27 backend and 13 frontend tests. Backend fixtures use SQLite setup but live routes still use JSON. The complete MapLibre workflow is manual only.

**Impact:**<br>
The most damaging defects can ship while the existing suite remains green—as demonstrated by reproducible lost updates and false readiness.

**Attack Scenario:**<br>
Not required; missing tests allow security and reliability regressions to pass release gates.

**How To Reproduce:**<br>
Run all tests, then run two application instances against one annotation file; the tests pass and data is still lost.

**Recommended Fix:**<br>
Add production-like Postgres integration, concurrency, Playwright browser, accessibility, load, security, migration/rollback, backup/restore, and failure-injection suites with enforced coverage and performance budgets.

**Example Fix:**<br>
Make the reproduced two-instance lost-update case a mandatory regression test after transactional persistence is implemented.

### PR-29 — API lifecycle and workflow rules are undefined

**File:** `backend/app/schemas/annotations.py:29-67`; `backend/app/routers/annotations.py`; all `/api` routes<br>
**Function/Class:** `AnnotationUpdate`; API contract<br>
**Severity:** 🟠 Major<br>
**Category:** API/Domain architecture — versioning, transitions, idempotency

**Problem:**<br>
The API has no version prefix, deprecation strategy, idempotency, optimistic concurrency, or workflow transition enforcement. Any supported status can change directly to any other. Creation timestamps exist, but no update/reviewer/event history does.

**Evidence:**<br>
All routes use `/api` rather than a versioned contract. `AnnotationUpdate` validates only membership in the status literal.

**Impact:**<br>
Clients cannot safely evolve, retries duplicate records, concurrent reviewers overwrite decisions, and audit/compliance questions cannot be answered.

**Attack Scenario:**<br>
An authorized user in a future system bypasses expected review stages or overwrites another review without detecting a conflict.

**How To Reproduce:**<br>
PATCH an annotation directly from `pending` to `rejected`, then back to `pending`; both requests succeed.

**Recommended Fix:**<br>
Version the public API, define a status state machine, store immutable transition events, require expected versions/ETags, and support idempotency keys for creates and report jobs.

**Example Fix:**

```http
If-Match: "annotation-version-7"
Idempotency-Key: 7a43...
```

### PR-30 — CORS and browser security policy are unsafe for a future authenticated deployment

**File:** `backend/app/main.py:61-69`; frontend hosting configuration (missing)<br>
**Function/Class:** `CORSMiddleware`<br>
**Severity:** 🟠 Major<br>
**Category:** Security — CORS, CSRF, browser headers

**Problem:**<br>
CORS allows credentials, all methods, and all headers for configured origins. There is no CSRF design, CSP, HSTS, frame-ancestors, permissions policy, or other browser security-header configuration. Localhost defaults are unsuitable as a production policy.

**Evidence:**<br>
`allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]` are hard-coded. No edge/header configuration exists.

**Impact:**<br>
When cookies or tokens are added, a permissive or misconfigured origin list can enable cross-origin abuse. Missing headers increase XSS/clickjacking impact.

**Attack Scenario:**<br>
A compromised allowed origin issues credentialed state-changing requests or embeds the application for clickjacking.

**How To Reproduce:**<br>
Send a preflight request from a configured origin and inspect allowed methods/headers; inspect normal responses for missing security headers.

**Recommended Fix:**<br>
Use exact production origins, least-privilege methods/headers, a deliberate token/cookie and CSRF model, and enforce security headers at the edge with automated tests.

**Example Fix:**

```python
allow_methods=["GET", "POST", "PATCH"],
allow_headers=["Authorization", "Content-Type", "If-Match"],
```

## Production Readiness Scorecard

| Category | Score /10 | Notes |
|---|---:|---|
| Security | 1 | No identity, authorization, tenancy, rate limiting, TLS boundary, audit trail, or hardened secrets. |
| Backend Architecture | 2 | Process-local store, non-transactional file writes, synchronous artifacts, unversioned API, and linear scans. |
| Frontend | 3 | Silent fallback deception, no request deadlines/runtime validation/error boundary, large initial data and bundle, inaccessible map workflows. |
| Database | 1 | Database is unused scaffolding; no migrations, spatial columns, constraints, tenant keys, or operational persistence. |
| Infrastructure | 1 | No full production deployment, TLS ingress, resource policy, hardened image, or private database boundary. |
| Reliability | 1 | Reproduced lost writes and false readiness; no idempotency, rollback, backups, or DR. |
| Scalability | 1 | 7.8 MB road payload per load, 13,520 DOM options, O(n) scans, and persistence that prevents multiple workers. |
| Testing | 4 | Existing tests pass but omit security, concurrency, production DB, load, E2E, accessibility, deployment, and recovery. |
| Observability | 0 | No structured logs, metrics, traces, error monitoring, audit events, dashboards, alerts, or SLOs. |
| AI Safety | N/A | No AI/LLM feature exists in the active repository; AI-specific runtime threats are currently outside the product surface. |

## Security Risk Matrix

| Finding | Severity | Likelihood | Impact | Primary risk |
|---|---|---:|---:|---|
| PR-01 No authentication/authorization/tenancy | 🔴 Critical | Certain if public | Critical | Data disclosure and arbitrary mutation |
| PR-02 Concurrent JSON lost updates | 🔴 Critical | High | Critical | Silent customer data loss |
| PR-03 Browser-only false saves | 🔴 Critical | High | Critical | Silent customer data loss |
| PR-04 Unbounded public writes/reports | 🔴 Critical | High | Critical | Memory/CPU/disk denial of service |
| PR-05 Non-transactional failed writes | 🔴 Critical | Medium | Critical | Divergent state and duplicates |
| PR-08 Default public PostgreSQL credentials | 🔴 Critical | High if Compose is exposed | Critical | Database compromise |
| PR-09 No secure production web boundary | 🔴 Critical | Certain at launch | Critical | Traffic interception and missing edge controls |
| PR-25 No CI/CD or rollback | 🔴 Critical | High | Critical | Uncontrolled releases and prolonged incidents |
| PR-26 No observability/audit | 🔴 Critical | Certain | Critical | Undetected attack/outage and no forensics |
| PR-27 No backups/DR | 🔴 Critical | Medium | Critical | Permanent data loss |
| PR-07 Source impersonation | 🟠 Major | High | Major | Fraudulent authoritative-looking records |
| PR-13 Unbounded/unauthorized reports | 🟠 Major | High | Major | Artifact disclosure, overwrite, disk exhaustion |
| PR-23 Unlocked/uncommitted dependency state | 🟠 Major | Medium | Major | Supply-chain compromise or broken rebuild |
| PR-30 Permissive future credentialed CORS | 🟠 Major | Medium | Major | Cross-origin authenticated abuse |

## Technical Debt Matrix

| Rank | Debt item | Principal | Interest paid today | Remediation size |
|---:|---|---|---|---|
| 1 | JSON/in-memory persistence | Data loss and no scaling | Every write and deployment | Large |
| 2 | Missing identity/tenant domain | Security and product model | Every endpoint and future feature | Large |
| 3 | Database facade without implementation | Misleading architecture | Every persistence decision | Large |
| 4 | No deployment/operations platform | Release and incident risk | Every release | Large |
| 5 | Full GeoJSON delivery and O(n) analysis | Latency and egress | Every page load/analysis | Large |
| 6 | Fabricated silent fallback | Data trust and duplicated logic | Every outage and contract change | Medium |
| 7 | Incomplete/unversioned datasets and heuristic | Incorrect customer decisions | Every report | Large |
| 8 | Report filesystem/in-memory lifecycle | Lost links and storage growth | Every restart/report | Medium |
| 9 | Missing CI/security/recovery tests | Regression risk | Every change | Medium |
| 10 | Frontend monolith/map synchronization | Performance and maintainability | Every UI feature | Medium |
| 11 | Unlocked Python/container supply chain | Rebuild drift | Every build | Medium |
| 12 | Unversioned API and no domain events | Client and audit debt | Every integration | Medium |

## Scalability Assessment

These estimates assume one cold application load per user and use only the measured 7.786 MB roads response. Other layer payloads, JavaScript, reports, retries, TLS overhead, and repeated use increase the totals.

| Scale | Roads transfer alone | Likely failure |
|---:|---:|---|
| 100 users | ~779 MB | Concurrent JSON writes can already lose data; browser selector/map lag appears; one API process becomes a bottleneck. |
| 1,000 users | ~7.8 GB | Serialization/bandwidth spikes, report/annotation contention, disk growth, and no safe second worker. |
| 10,000 users | ~77.9 GB | Architecture is nonviable: worker saturation, egress cost, long browser tasks, widespread lost updates. |
| 100,000 users | ~778.6 GB | Service cannot operate; no safe horizontal scaling, cache/CDN, indexed queries, or tenant isolation. |
| 1,000,000 users | ~7.8 TB | Complete failure and prohibitive egress; file persistence and single-process state make this scale impossible. |

Database performance cannot be credibly estimated at these levels because runtime traffic does not use the database. If the current minimal models were activated, JSON geometry and missing spatial/tenant indexes would still make production spatial queries and isolation unacceptable.

## Missing Systems Report

| Priority | Missing system | Consequence |
|---|---|---|
| P0 | Authentication, authorization, roles, tenant isolation | Public data disclosure and arbitrary mutation |
| P0 | Transactional PostgreSQL/PostGIS persistence | Lost updates, no multi-worker scaling |
| P0 | Immutable audit/event history | No accountability or forensics |
| P0 | HTTPS ingress, rate/body limits, WAF/security headers | Interception, abuse, and DoS exposure |
| P0 | CI/CD with protected gates and rollback | Unsafe, non-reproducible releases |
| P0 | Structured observability and alerting | Undetected incidents and attacks |
| P0 | Backups, PITR, restore drills, DR runbook | Permanent customer data loss |
| P0 | True liveness/readiness/startup checks | Broken instances receive traffic |
| P1 | Database migrations and rollback tests | Unsafe schema evolution |
| P1 | Data ingestion staging, provenance, freshness, quality gates | Stale/incorrect planning evidence |
| P1 | Report job queue, durable metadata, object storage, retention | Lost/overwritten reports and disk exhaustion |
| P1 | Idempotency, optimistic concurrency, state-machine rules | Duplicates and overwritten reviews |
| P1 | Runtime API contract validation/generated client | Frontend crashes and contract drift |
| P1 | Browser E2E, accessibility, load, security, failure tests | Production defects remain invisible |
| P1 | Vector tile/viewport delivery and corridor search | Unsustainable bandwidth and browser performance |
| P1 | Feature flags and safe configuration promotion | Risky releases and environment drift |
| P2 | Usage/cost analytics and capacity dashboards | No product or infrastructure cost control |
| P2 | Queue/storage monitoring and quota management | Unbounded background/storage cost |
| N/A | AI/LLM security controls | No AI runtime exists; required before any AI feature is introduced |

## Top 20 Fixes by ROI

| Rank | Fix | Effort | Impact |
|---:|---|---:|---:|
| 1 | Disable fallback for POST/PATCH and remove false “saved” messages | Low | Critical |
| 2 | Add request-body, geometry-vertex, rate, and report limits | Low–Medium | Critical |
| 3 | Remove client-controlled `source`; default new stores to empty | Low | Major |
| 4 | Commit the Nano ID lock update and add dependency/security scanning | Low | Major |
| 5 | Add `.dockerignore` and run the container as non-root | Low | Major |
| 6 | Make report format a literal and switch IDs to UUIDs | Low | Major |
| 7 | Add real readiness checks and fail on required dependency failure | Low–Medium | Critical |
| 8 | Add mandatory CI with no skipped required checks | Medium | Critical |
| 9 | Put the current deployment behind HTTPS with strict origins, body limits, and security headers | Medium | Critical |
| 10 | Add identity-aware gateway protection and temporarily deny all public writes | Medium | Critical |
| 11 | Add structured request/error/security logs and alerts | Medium | Critical |
| 12 | Add browser request timeouts, cancellation, and explicit degraded state | Medium | Major |
| 13 | Split MapLibre source updates and replace the 13,520-option selector | Medium | Major |
| 14 | Establish automated encrypted backups and prove restore | Medium | Critical |
| 15 | Introduce Alembic and tenant-aware PostgreSQL/PostGIS schema | Large | Critical |
| 16 | Migrate annotations to transactional repositories with audit/version fields | Large | Critical |
| 17 | Move report metadata/artifacts to database/object storage with retention | Medium–Large | Major |
| 18 | Replace full road GeoJSON with tiles/viewport delivery and caching | Large | Critical at scale |
| 19 | Replace rectangle scans with indexed PostGIS distance queries | Large | Major |
| 20 | Add Playwright, concurrency, load, accessibility, migration, and recovery gates | Large | Critical |

## Top 10 Production Blockers

1. No authentication, authorization, roles, or tenant isolation.
2. Reproducible concurrent-write data loss in the JSON store.
3. Silent browser-only writes presented as saved.
4. Unbounded unauthenticated annotation and report abuse.
5. No secure full-stack production deployment or TLS boundary.
6. No transactional production database path or migrations.
7. No CI/CD, immutable artifacts, environment promotion, or rollback.
8. No observability, audit logging, monitoring, or alerting.
9. No backup, restore, retention, or disaster-recovery system.
10. Incomplete/approximate data and analysis presented as customer-facing decision labels.

## 30-Day Remediation Plan

### Week 1 — Stop data loss and close public attack paths

- Disable mutation fallback and remove all false saved states.
- Put the API behind temporary authenticated access; deny anonymous writes and report generation.
- Enforce body, vertex, request-rate, and storage limits.
- Remove client-controlled source and demo annotation seeding.
- Commit the Nano ID update; add `.dockerignore`; run containers non-root.
- Restrict PostgreSQL to a private network and require injected secrets.
- Add CI for tests, build, audits, lint/type checks, data validation, secret scanning, and container startup.
- Add real readiness and startup-failure logging.

**Exit gate:** No anonymous mutation, no browser-only “saved” write, no default database credential, and no merge without required CI.

### Week 2 — Establish transactional identity-aware persistence

- Define organization, user, role, and record-ownership rules.
- Create Alembic migrations for tenant-aware PostgreSQL/PostGIS tables.
- Add UUIDs, foreign keys, checks, audit/version fields, and spatial indexes.
- Implement authenticated repositories and transaction boundaries.
- Build and test JSON-to-database migration with rollback.
- Add idempotency keys and optimistic concurrency.
- Persist report metadata and use controlled artifact storage.

**Exit gate:** Multi-worker concurrency tests pass without lost updates; every mutation has an actor, tenant, transaction, and audit event.

### Week 3 — Correct data delivery, analysis, and frontend failure behavior

- Stage/validate/version GIS ingestion with provenance and anomaly thresholds.
- Replace approximate bbox proximity with indexed PostGIS queries.
- Remove unapproved feasibility/priority labels or complete formal validation/governance.
- Deliver roads by tile/viewport and add server-backed corridor search.
- Split map source updates, lazy-load MapLibre, and enforce bundle/performance budgets.
- Add request timeout/cancellation, runtime schemas, error boundary, and visible data mode.
- Implement keyboard-equivalent geometry workflows.

**Exit gate:** Results identify dataset/method versions; browsers do not download all roads; outages cannot masquerade as live data.

### Week 4 — Prove operability and launch controls

- Deploy full stack to staging behind HTTPS with security headers and strict CORS.
- Add structured logs, metrics, traces, error tracking, dashboards, SLOs, and alerts.
- Configure encrypted PITR backups/object versioning and perform a restore drill.
- Run security, authorization, tenant-isolation, load, Playwright, accessibility, migration/rollback, and failure-injection tests.
- Add signed immutable artifacts, staged promotion, canary/rollback automation, and incident runbooks.
- Conduct an independent security review and launch-gate re-audit.

**Exit gate:** Backup restore and rollback are demonstrated; security/load/SLO gates pass; all Critical findings are closed with evidence.

Thirty days is an aggressive stabilization window, not an automatic launch date. Any unresolved Critical finding keeps the release blocked.

## Final Verdict

# NOT PRODUCTION READY

CURBO cannot safely serve paying customers. The audit reproduced silent lost updates, false healthy status with a failed configured database, unbounded large input acceptance, spoofed source attribution, report format/ID failures, and a multi-megabyte per-user road response. These are not theoretical scaling concerns; they occur in the current implementation.

Production launch must remain blocked until the Top 10 Production Blockers are resolved and independently verified in a production-like environment. Passing the current 40 automated tests does not offset missing access control, transactional persistence, secure deployment, observability, backups, or concurrency/load/security coverage.
