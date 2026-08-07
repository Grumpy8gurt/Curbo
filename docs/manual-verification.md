# CURBO Manual Verification

This document records the important checks performed by a person using the real application. Automated tests cover exact rules and edge cases; manual checks confirm that the complete browser workflow looks and behaves correctly.

## Sprint 4 result

Sprint 4 completed the annotation-review workflow. A reviewer can create a note, change its status, restart the backend, and still see the saved decision. Corridor evidence and reports also reflect the current review status.

The manual checks used temporary annotation and report files, so normal repository data was not changed.

### Manual checks

| Check | What happened | Result |
|---|---|---|
| Load the application | The browser displayed 13,520 roads and 400 features in each of the ramp, hydrant, and bicycle layers. | Pass |
| Create an annotation | A new bike-gap note was saved, selected on the map, and included in the selected corridor. | Pass |
| Reject an annotation | The rejected note stayed in history but stopped increasing active concern counts. | Pass |
| Confirm an annotation | A confirmed parking conflict remained active but no longer counted as needing review. | Pass |
| Restart the backend | The rejected and confirmed statuses were still present after a new backend process started. | Pass |
| Generate a report | The HTML report downloaded and contained readable metrics, review signals, notes, and limitations. | Pass |
| Check mobile layout | At 390×844, the page had no horizontal overflow and the map legend stayed inside the map. | Pass |
| Check visible language | The interface used permanent CURBO planning language rather than development or release terminology. | Pass |

### Automated checks

Run all existing checks from the repository root:

```bash
./scripts/verify_sprint4.sh
```

Verified results:

- 27 backend tests passed.
- 13 frontend tests passed in 7 files.
- The frontend production build passed.
- `npm audit` reported no known vulnerabilities.
- All 7 GeoJSON files passed validation.
- Docker Compose configuration was valid.

### Important problems found and fixed

| Problem | Fix | How it was checked |
|---|---|---|
| Users could not change annotation status from the map. | Added the status selector and PATCH request. | Component, API, persistence, and browser checks passed. |
| Explicit GeoJSON could contain impossible coordinates. | Applied one coordinate validator to points and every line position. | Longitude or latitude `999` now returns HTTP 422. |
| Rejected notes still affected active corridor concerns. | Kept them in history but excluded them from active counts. | Automated status tests and the browser workflow passed. |
| Corridor results and report links could become stale. | Refreshed the selected corridor after changes and ignored older responses. | API/component tests and browser status messages passed. |
| Ramp measurements were being discarded or misread. | Preserved aggregate and left/right measurements and hid invalid width sentinels. | Backend normalization and frontend boundary tests passed. |
| Reports displayed raw Python data. | Replaced it with labeled, escaped HTML sections. | Report tests and a real downloaded report passed. |
| The frontend had no automated test runner. | Added Vitest, jsdom, and Testing Library. | All 13 frontend tests passed. |
| The mobile legend could overlap the page. | Kept the map as the legend's positioned container. | The 390×844 follow-up check passed. |

### Remaining limits

- Annotations are stored in one JSON file. This is suitable for one user and one backend process, not concurrent production use.
- There is no authentication or authorization.
- Ramp measurements are screening information, not accessibility-compliance findings.
- Corridor review attention is a simple, documented heuristic. It is not a safety or project-priority score.
- The cached data is not fully current or complete: roads are a complete dated snapshot, while the other layers are 400-feature extracts.
- Delete and geometry editing are not included.
- The frontend build still reports a non-blocking large MapLibre bundle warning.

## Sprint 3 summary

Sprint 3 established the base that Sprint 4 improved:

- removed the old ML/image-detection workflow;
- loaded cached Eugene GIS data without requiring a live City service;
- expanded the road cache to all 13,520 segments and added road labels;
- added point and line annotations with JSON persistence;
- added corridor summaries and HTML reports;
- handled `MultiLineString` features and proper bounding-box intersections; and
- kept PostGIS optional rather than making it a startup requirement.

Sprint 3 verification included backend tests, a frontend production build, dependency audit, GeoJSON validation, cache-only refresh checks, Compose validation, and connected browser use. Its remaining limitations—single-user JSON persistence, dated cached data, optional database scaffolding, and incomplete production deployment—still apply.
