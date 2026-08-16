# CURBO Data Model

Sprint 5 uses two kinds of data:

- read-only civic GIS layers loaded from cached GeoJSON; and
- writable reviewer annotations and report metadata stored transactionally in PostgreSQL when configured.

A locked JSON annotation file remains available for simple local development. Production requires the database path and current Alembic revision.

## Civic GIS collections

`data/eugene/` is the normal offline runtime cache.

| Collection | Geometry | Important normalized properties |
| --- | --- | --- |
| Roads | `LineString` or `MultiLineString` | `road_id`, `name`, `classification`, `source` |
| Sidewalk ramps | `Point` | `ramp_id`, status, condition, configuration, aggregate/left/right width, grade, and cross-slope values |
| Hydrants | `Point` | `hydrant_id`, owner, flow class, source |
| Bicycle facilities | `LineString` or `MultiLineString` | `bike_lane_id`, name, facility type, status, source |

Published ramp widths are stored in feet and grades/slopes as percentages. Null source values remain null. Nonpositive width sentinels become null, but a measured 0% slope remains meaningful.

Every runtime layer is a GeoJSON `FeatureCollection`. `EugeneDataService` translates changing source field names into the stable properties used by the API and frontend.

## Annotation record

An annotation is a reviewer note, not an authoritative change to the City inventory.

| Field | Meaning |
| --- | --- |
| `id` | UUID-based annotation identifier |
| `type` | Controlled observation category |
| `description` | Human reviewer explanation |
| `status` | `pending`, `reviewed`, `confirmed`, or `rejected` |
| `source` | Server-assigned reviewer source; clients cannot claim an authoritative source |
| `geometry` | Valid GeoJSON `Point` or `LineString` |
| `idempotency_key` | Optional unique key that makes create retries safe |
| `version` | Optimistic concurrency version, beginning at 1 |
| `created_at` | Creation time |
| `updated_at` | Last database update time |

Allowed status transitions are:

```text
pending  -> reviewed, confirmed, or rejected
reviewed -> confirmed or rejected
confirmed -> terminal
rejected  -> terminal
```

The client sends `expectedVersion` when changing status. A stale version or invalid transition returns HTTP 409 and does not replace the stored state.

## Corridor report record

| Field | Meaning |
| --- | --- |
| `id` | UUID-based report identifier |
| `road_id` | Road used for the corridor analysis |
| `include_layers` | Requested evidence layers |
| `summary` | Stored analysis metadata |
| `format` | `html`; no other format is accepted |
| `download_path` | Server-controlled artifact path |
| `created_at` | Report creation time |

The HTML artifact is written atomically to the configured report directory. Download lookup uses stored metadata and verifies that the resolved file remains inside that directory. Retention removes expired or excess report files.

## Database constraints and indexes

The Alembic migration creates:

- primary keys for annotations and reports;
- a unique idempotency key constraint;
- annotation status and report format check constraints;
- annotation indexes on type, creation time, and status plus creation time; and
- report indexes on road and creation time.

The database currently stores JSON geometry rather than PostGIS geometry. This is enough for transactional reviewer persistence, but spatial indexes and GIS-layer database ingestion remain future scalability work.

## Local-development file format

Without `DATABASE_URL`, annotations are stored as a JSON array in the configured `ANNOTATION_FILE`. Each object mirrors the database domain fields. File access uses thread/process locks and atomic replacement. A corrupt existing file causes startup failure and is not silently overwritten. A missing file starts as an empty annotation list.

## Derived corridor state

Corridor analysis recalculates nearby state for each request:

- `userAnnotationsNearby` includes every nearby annotation status as history;
- active concern counts exclude rejected annotations;
- `annotationsNeedingReview` counts active pending annotations; and
- confirmed observations remain active evidence but no longer need review.

Derived counts, review signals, attention, notes, and limitations are not persisted as an authoritative score. Reports request fresh analysis before rendering.

## Production data boundary

Production startup can require every civic layer to report `cached-eugene` status and meet configured minimum counts. This is a technical completeness gate, not proof that the source is current, legally sufficient, or suitable for a compliance determination.

Future high-scale work should import governed GIS layers into PostGIS using native geometry columns, spatial indexes, source revisions, licensing/provenance records, and controlled refresh jobs.
