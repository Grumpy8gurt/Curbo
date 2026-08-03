# CURBO Data Model

Sprint 4 retains the Sprint 3 GeoJSON and JSON persistence model while carrying
curb-ramp measurements through normalization and completing annotation status
updates. PostgreSQL/PostGIS remains planned long-term infrastructure.

## Sprint 3 Runtime Data

- `data/eugene/roads.geojson` maps source identifiers and names to `road_id`, `name`, and `classification`.
- `data/eugene/sidewalk_ramps.geojson` maps the City ramp inventory to `ramp_id`, `status`, `condition`, `configuration`, width values in feet, and grade/cross-slope values in percent. Null source measurements remain null. The backend keeps `/api/layers/curb-ramps` as a compatibility alias.
- `data/eugene/hydrants.geojson` maps source identifiers to `hydrant_id`, `owner`, and `flow_class`.
- `data/eugene/bike_lanes.geojson` maps bicycle facilities to `bike_lane_id`, `name`, `facility_type`, and `status`.
- User annotations persist as GeoJSON-compatible `Point` or `LineString` records in `backend/data/annotations.json` using atomic replacement writes. Their review status is one of `pending`, `reviewed`, `confirmed`, or `rejected`. They are a reviewer-notes overlay and do not modify or augment the authoritative Eugene infrastructure collections.

The JSON annotation store is intentionally single-user. It provides demonstrable persistence without introducing a database migration into the civic-data integration scope.

## Planned PostGIS Model

The future database can use the following domain tables and geometry expectations.

## Core Infrastructure Tables

- `roads`: street centerlines or segments used for corridor analysis; suggested geometry type `LINESTRING` or `MULTILINESTRING`
- `sidewalks`: sidewalk network segments for accessibility review; suggested geometry type `LINESTRING` or `MULTILINESTRING`
- `curb_ramps`: known curb ramp locations and attributes; suggested geometry type `POINT`
- `hydrants`: hydrant inventory for map context and right-of-way review; suggested geometry type `POINT`
- `parking_zones`: curbside parking regulations or zones; suggested geometry type `LINESTRING` or `POLYGON`
- `bike_lanes`: bicycle facility segments; suggested geometry type `LINESTRING`
- `bus_routes`: transit route alignments; suggested geometry type `LINESTRING`
- `bus_stops`: transit stop inventory; suggested geometry type `POINT`
- `parcels`: parcel boundaries for land context; suggested geometry type `POLYGON` or `MULTIPOLYGON`
- `driveways`: driveway crossings or access points; suggested geometry type `LINESTRING` or `POINT`

## User and Workflow Tables

- `annotations`: planner-created notes, flags, or sketch geometry; currently points and lines, with suggested future geometry type `GEOMETRY` if polygons are added
- `corridor_reports`: generated summary records and artifact metadata; suggested geometry type `LINESTRING` or `POLYGON` for corridor footprint, nullable if stored indirectly
