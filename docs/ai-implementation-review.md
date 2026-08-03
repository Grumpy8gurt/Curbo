# Sprint 4 AI Implementation Review

## AI-Assisted Test Generation

AI generated focused backend cases for out-of-range explicit GeoJSON, a missing
annotation PATCH target, and Eugene curb-ramp measurement normalization. It
also extended coverage for restart-persisted review status, active versus
rejected corridor concerns, readable report output, width sentinels, side-specific
grades, dimensional reference boundaries, dynamic offline behavior, the report
panel, and the corridor API contract.

## AI-Assisted Test Review

Generated assertions were checked against the actual Pydantic schemas,
FastAPI responses, React state flow, and Eugene field names. A proposed
whole-application frontend test was rejected because MapLibre/WebGL setup would
make the test brittle while adding little coverage of the changed workflow.
It was replaced with component and API tests that directly verify the user's
status selection and its network effect. The final suite has 27 backend tests
and 9 frontend tests across 6 frontend files.

## Refactoring Decision

Accepted: extract one `validate_position` function and use it for Point and
every LineString position. This removes divergent input rules while preserving
the existing schemas. Accepted: keep one status-aware corridor calculation and
share its response shape with the frontend type, fallback builder, report
panel, and HTML export. Accepted: use a pure curb-ramp helper so reference
boundaries can be tested without mounting MapLibre. Rejected: add Delete,
geometry editing, routing, live crash ingestion, or a compliance result in the
same sprint; those require new product rules, sources, and governance.

## Verification of AI-Generated Work

The work was not accepted from source review alone. The complete verifier
passed 27 backend tests, 9 frontend tests, the production build, a zero-vulnerability
dependency audit, seven GeoJSON validations, and Docker Compose configuration.
A connected browser session loaded the full cached layers, created and rejected
a bike-gap note, created and confirmed a parking conflict, regenerated the
selected-corridor evidence, created and downloaded an HTML report, and proved
both review states survived a fresh backend process. A 390×844 visual pass
found and corrected a mobile legend-positioning defect; a follow-up pass showed
no horizontal overflow and kept the legend inside the map.

---

## Sprint 3 AI Implementation Review

## How AI Assisted Sprint 3 Implementation

AI assisted with repository-wide dependency tracing, City of Eugene GIS source research, GeoJSON normalization design, point and line annotation support, `MultiLineString` handling, road-label glyph bundling, API contract cleanup, frontend type alignment, test updates, and documentation drafting. The implementation evolved the existing frontend/backend foundation rather than replacing the project.

## How AI-Assisted Engineering Review Was Used

AI-assisted review compared the active routes, frontend imports, Docker configuration, documentation, and generated artifacts against the Sprint 3 scope. Runtime tests and source searches were then used to verify the suggestions instead of accepting them without evidence.

## Accepted Suggestion

Accepted: Focus Sprint 3 on City of Eugene GIS integration instead of adding unrelated new features. A committed local cache and optional refresh script provide a meaningful expansion without making normal startup depend on an external service.

## Rejected or Postponed Suggestion

Rejected/Postponed: Keeping the ML curb-cut detection layer, because Sprint 3 is better scoped around civic data integration and maintainable architecture. A full PostGIS import was also postponed because cached GeoJSON plus lightweight corridor analysis is sufficient for this prototype.

## Human Engineering Decision

Human decision: Rename the project to CURBO and remove the ML layer to keep the prototype aligned with Sprint 3's manageable expansion requirement. The human developer also chose JSON-file annotation persistence as an inspectable intermediate step before multi-user database persistence.

## Verification After AI-Assisted Review

AI findings were checked with backend tests, a frontend production build and dependency audit, GeoJSON validation, cache-only refresh verification, Compose validation, browser-based corridor/report flows, and a clean-clone test. The later road-layer review also verified all 13,520 cached segments, unique normalized IDs, directional street names, and the locally bundled MapLibre label glyph. Suggestions that were not supported by those checks were not treated as application defects.
