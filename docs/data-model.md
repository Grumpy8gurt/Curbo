# Planned Data Model

The database will use PostgreSQL with PostGIS. Table definitions are still to be implemented, but these are the intended domain tables and geometry expectations.

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

- `annotations`: planner-created notes, flags, or sketch geometry; suggested geometry type `GEOMETRY` to allow points, lines, and polygons
- `detections`: curb-cut detection outputs with confidence and review status; suggested geometry type `POINT` or `POLYGON`
- `uploaded_images`: metadata for uploaded street-level imagery and storage references; suggested geometry type `POINT` when geolocated, nullable at first
- `corridor_reports`: generated summary records and artifact metadata; suggested geometry type `LINESTRING` or `POLYGON` for corridor footprint, nullable if stored indirectly
