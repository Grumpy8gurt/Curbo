# Sprint 2 AI Implementation And Review Note

## How AI Helped Implementation

AI helped accelerate repository setup, frontend scaffolding, backend route integration, and documentation drafting. It was most useful for:

- organizing the frontend into components, API modules, and typed data flow
- drafting mock-first FastAPI routes and response schemas
- identifying request and response mismatches between frontend and backend
- helping summarize the implementation and Sprint 2 boundaries in documentation

## How AI Helped Review

AI was also used as a review assistant to compare frontend expectations against backend behavior, inspect runtime errors, point out brittle integration points, and summarize what was working versus what was still incomplete. Some suggestions were useful, but the review quality was mixed, and several outputs still needed human correction and verification.

## One Suggestion I Accepted

I accepted the suggestion to keep the frontend and backend compatible by adjusting request and response handling instead of rewriting the whole stack. That kept the Sprint 2 scope focused while still producing one coherent client/server feature slice.

## One Suggestion I Rejected Or Postponed

I postponed replacing the mock-first data flow with full Postgres/PostGIS persistence so the Sprint 2 work could remain focused on the core planning workflow.

## One Verification Step After Review

After AI-assisted review surfaced integration drift and runtime issues, I verified the current prototype by running:

- `cd frontend && npm run build`
- `cd backend && pytest`

I also confirmed that the backend could start locally with `uvicorn`, checked key backend routes with smoke tests, and re-tested the frontend map after replacing its remote basemap dependency.

## Final Responsibility

AI helped with implementation speed, issue discovery, and drafting, but final engineering decisions remained my responsibility. I decided which suggestions to keep, which to reject or postpone, and whether the results were acceptable based on build output, test results, startup behavior, and the actual state of the repository.

## Sprint 3 AI Implementation Review

### How AI Assisted Sprint 3 Implementation

AI assisted with repository-wide dependency tracing, City of Eugene GIS source research, GeoJSON normalization design, API contract cleanup, frontend type alignment, test updates, and documentation drafting. The implementation remained an extension of the Sprint 2 codebase rather than a replacement project.

### How AI-Assisted Engineering Review Was Used

AI-assisted review compared the active routes, frontend imports, Docker configuration, documentation, and generated artifacts against the Sprint 3 scope. Runtime tests and source searches were then used to verify the suggestions instead of accepting them without evidence.

### Accepted Suggestion

Accepted: Focus Sprint 3 on City of Eugene GIS integration instead of adding unrelated new features. A committed local cache and optional refresh script provide a meaningful expansion without making normal startup depend on an external service.

### Rejected or Postponed Suggestion

Rejected/Postponed: Keeping the ML curb-cut detection layer, because Sprint 3 is better scoped around civic data integration and maintainable architecture. A full PostGIS import was also postponed because cached GeoJSON plus lightweight corridor analysis is sufficient for this prototype.

### Human Engineering Decision

Human decision: Rename the project to CURBO and remove the ML layer to keep the prototype aligned with Sprint 3's manageable expansion requirement. The human developer also chose JSON-file annotation persistence as an inspectable intermediate step before multi-user database persistence.

### Verification After AI-Assisted Review

AI findings were checked with backend tests, a frontend production build and dependency audit, GeoJSON validation, cache-only refresh verification, Compose validation, browser-based corridor/report flows, and a clean-clone test. Suggestions that were not supported by those checks were not treated as application defects.
