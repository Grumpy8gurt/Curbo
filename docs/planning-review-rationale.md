# Planning and Bicycling Review Rationale

This note records the external research used to choose CURBO's Sprint 4
quality improvements. It is design evidence, not a claim that CURBO performs a
traffic-engineering study, an accessibility audit, or a regulatory compliance
determination.

## What Matters to City Reviewers and People Biking

### Network continuity and documented concerns

Eugene's active-transportation strategy emphasizes a connected, low-stress
walking and bicycling network, closing network gaps, improving crossings,
retrofitting curb ramps, and maintaining facilities. NACTO likewise treats a
connected network as the unit of planning rather than evaluating isolated
segments. This supports improving CURBO's existing corridor workflow so a
reviewer can see bicycle-network gaps, intersection-safety concerns, and
parking/loading conflicts together.

Sources:

- [MoveEUG: Eugene Active Transportation Strategy](https://www.eugene-or.gov/DocumentCenter/View/39679/MoveEUG_Eugene-Active-Transportation-Strategy_2017)
- [NACTO: Components of a Connected Bike Network](https://nacto.org/latest/urban-bikeway-design-guide-components-of-a-connected-bike-network/)
- [NACTO: Planning a Bike Network](https://nacto.org/publication/urban-bikeway-design-guide/planning-and-developing-a-bikeable-city/planning-a-bike-network/)

### Risk-based review without pretending to rank projects

Eugene's Vision Zero program publishes a High Crash Network and reports that a
small share of streets accounts for most fatal and serious-injury crashes.
FHWA's pedestrian and bicyclist road-safety-audit guidance also combines
community observations with roadway, midblock, and intersection review.
Those practices support an explainable review-attention signal, but CURBO does
not have enough current crash, speed, volume, or exposure data to produce a
safety score or funding priority.

Sources:

- [City of Eugene Vision Zero](https://www.eugene-or.gov/4270/Vision-Zero)
- [Eugene High Crash Network for People Biking](https://www.eugene-or.gov/DocumentCenter/View/83215/HCN-for-People-Biking)
- [FHWA Pedestrian and Bicyclist Road Safety Audit Guide](https://highways.dot.gov/sites/fhwa.dot.gov/files/2022-08/fhwasa20042.pdf)

### Context matters for bicycle-facility decisions

FHWA's bikeway-selection guidance considers motor-vehicle speed and volume,
roadway context, and intended users. Parking, right-of-way, intersection
conditions, and field observations also affect feasibility. CURBO therefore
keeps its existing feasibility value explicitly preliminary and lists the
missing decision inputs in every corridor response and generated report.

Source: [FHWA Bikeway Selection Guide](https://highways.dot.gov/sites/fhwa.dot.gov/files/2022-07/fhwasa18077.pdf)

### Accessibility measurements are useful screening evidence

The U.S. Access Board's Public Right-of-Way Accessibility Guidelines include
dimensional references such as a 4-foot minimum clear width for curb-ramp runs,
a maximum 1:12 running slope, and generally a maximum 1:48 cross slope. CURBO
can use published width and slope measurements to prompt field review. It
cannot decide compliance because source age, measurement method, site geometry,
exceptions, alterations, and applicable law still require professional review.

Source: [U.S. Access Board PROWAG](https://www.access-board.gov/prowag/complete.html)

### Maintenance and rider-reported hazards are operational evidence

FHWA maintenance guidance and Eugene's bike-hazard reporting workflow show
that surface conditions, obstructions, and other field observations matter to
people using a bikeway after it is built. CURBO's existing annotation types
already support obstructions, drainage/utility conflicts, bad data, and other
notes, so Sprint 4 strengthens review status and reporting instead of creating
a separate issue-management system.

Sources:

- [FHWA Guide for Maintaining Active Transportation Infrastructure](https://highways.dot.gov/sites/fhwa.dot.gov/files/2024-10/Guide_for_Maintaining_Active_Transportation_FHWA-SA-23-005.pdf)
- [City of Eugene Bike Hazard Reporting](https://www.eugene-or.gov/1943/Bike-Hazard)

## Changes Chosen for CURBO

| Research implication | Sprint 4 implementation | Quality benefit |
|---|---|---|
| Review connected concerns, not only inventory totals | Corridor analysis counts active bike-lane gaps, intersection-safety observations, parking/loading conflicts, missing curb cuts, and annotations needing review | Existing annotations become decision-support evidence without creating a new workflow |
| Distinguish unresolved evidence from rejected notes | Rejected annotations remain in the audit trail but do not increase active concern counts or review attention | Status updates have a visible, testable effect |
| Make a screen explainable | The API returns `reviewPriority`, human-readable `reviewSignals`, and a data-limitation disclaimer | Reviewers can see why a corridor was flagged and what CURBO does not know |
| Preserve useful field measurements | Left/right curb-ramp grades are normalized with widths and cross slopes; impossible nonpositive width sentinels become null | Published data is no longer discarded, while absent values do not become false alerts |
| Avoid compliance overstatement | Measurements outside PROWAG reference values produce field-review prompts with an explicit disclaimer | The interface is actionable without presenting a legal or engineering conclusion |
| Support review meetings and handoff | The HTML report uses labeled metrics, signals, notes, and limitations instead of a raw dictionary dump | Generated evidence is readable and maintainable |
| Reduce operator error | The frontend clarifies dashboard hierarchy, keyboard focus, activity announcements, layer state, and responsive layout | The existing map workflow is easier to scan and use |

The Low/Medium/High review-attention weights are a CURBO prototype heuristic,
not values taken from these sources. Bike-lane-gap and intersection-safety
observations receive 2 points each (capped at two observations per category);
parking/loading conflicts and missing curb cuts receive 1 point each (also
capped at two); and the absence of an intersecting mapped bicycle facility adds
1 point. Scores 0–1 are Low, 2–3 are Medium, and 4 or more are High. The API
returns the contributing signals so the result can be challenged rather than
treated as an opaque ranking.

## Explicit Scope Guardrails

Sprint 4 does not add turn-by-turn routing, live crash-data ingestion, a project
ranking or equity score, crowdsourced accounts, image uploads, or a new
database. It also does not label a curb ramp compliant or noncompliant. Future
work could add official High Crash Network overlays, bicycle-facility-type
styling, and richer maintenance tracking after source freshness, provenance,
and product rules are defined.
