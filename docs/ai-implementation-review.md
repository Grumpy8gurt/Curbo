# CURBO AI Implementation Review

This document explains how AI assistance was used and how its work was checked. AI suggestions were not accepted only because they looked reasonable; they were compared with the real code and verified with tests or browser checks.

## Sprint 4

### What AI helped with

AI helped identify missing tests and quality gaps around:

- invalid point and line coordinates;
- unknown annotation IDs;
- annotation status surviving a backend restart;
- rejected versus active corridor concerns;
- ramp measurement normalization;
- readable report output;
- frontend API and component behavior; and
- product-facing language and mobile presentation.

### Test decisions

Accepted tests included:

- explicit longitude or latitude outside the valid world range returns HTTP 422;
- a changed annotation status is still present after a fresh backend starts;
- rejected notes remain in history but stop affecting active concerns;
- confirmed notes remain active;
- zero width sentinels are hidden while a valid 0% slope is preserved; and
- reports contain readable sections and screening limitations.

A proposed whole-application frontend test was rejected. It required large MapLibre and WebGL mocks, so it would mostly test the mocks instead of the review workflow. It was replaced with smaller component and API tests, while the complete map workflow was checked in a real browser.

### Refactoring decisions

Three maintainability improvements were accepted:

1. One `validate_position` helper now validates Point coordinates and every LineString position.
2. One backend corridor calculation produces the status-aware result mirrored by frontend types, fallback data, the report panel, and HTML reports.
3. A pure ramp-review helper makes width and slope boundaries testable without starting MapLibre.

Features such as deletion, geometry editing, routing, live crash-data ingestion, and compliance decisions were left out. They require additional product rules, data sources, security, and governance.

### How the work was verified

The final verification included:

- 27 passing backend tests;
- 13 passing frontend tests;
- a successful production build;
- no known npm vulnerabilities;
- 7 valid GeoJSON files;
- valid Docker Compose configuration;
- a connected browser create/reject/confirm workflow;
- a backend restart that preserved review statuses;
- a real report download; and
- a 390×844 mobile layout check.

The browser check found a mobile legend-positioning problem. The layout was corrected and checked again, demonstrating why manual review was kept alongside automated tests.

## Sprint 3 summary

AI also assisted Sprint 3 with repository review, Eugene GIS normalization, point and line annotations, `MultiLineString` support, road labels, API alignment, tests, and documentation.

The main human decisions were to:

- focus CURBO on civic GIS rather than keep the earlier ML workflow;
- use a committed local cache so startup does not depend on the City service; and
- use inspectable JSON persistence temporarily instead of completing PostGIS in the same sprint.

These decisions were checked with backend tests, frontend build and audit, GeoJSON validation, cache-preservation checks, Compose validation, browser workflows, and a clean-clone review. Unsupported AI suggestions were not treated as defects or requirements.
