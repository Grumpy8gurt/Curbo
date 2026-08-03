# Sprint 4 AI Implementation Review

## AI-Assisted Test Generation

AI generated focused backend cases for out-of-range explicit GeoJSON, a missing
annotation PATCH target, and Eugene curb-ramp measurement normalization. It
also introduced the frontend test harness and tests for the review selector,
dimension rendering, and the PATCH request contract.

## AI-Assisted Test Review

Generated assertions were checked against the actual Pydantic schemas,
FastAPI responses, React state flow, and Eugene field names. A proposed
whole-application frontend test was rejected because MapLibre/WebGL setup would
make the test brittle while adding little coverage of the changed workflow.
It was replaced with component and API tests that directly verify the user's
status selection and its network effect.

## Refactoring Decision

Accepted: extract one `validate_position` function and use it for Point and
every LineString position. This removes divergent input rules while preserving
the existing schemas. Rejected: add Delete and geometry editing in the same
sprint. Those operations require new product rules and would broaden a
narrowly scoped completion of the existing Update workflow.

## Verification of AI-Generated Work

The work was not accepted from source review alone. The backend suite passed
23 tests, the new frontend suite passed 3 tests, the production build passed,
and a connected browser session created an annotation and persisted a status
change from `pending` to `reviewed`. The browser result and API behavior were
compared with the documented expected effects.

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
