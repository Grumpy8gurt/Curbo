# City of Eugene GIS Cache

This directory contains the local GeoJSON cache used by CURBO Sprint 3. The files are downloaded from public, API-key-free City of Eugene ArcGIS REST layers and retained in the repository so the demo does not require network access.

| CURBO layer | City service layer |
|---|---|
| `roads.geojson` | [Transportation — Streets (2)](https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/2) |
| `sidewalk_ramps.geojson` | [Transportation — Existing Ramps (29)](https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/29) |
| `hydrants.geojson` | [Miscellaneous Infrastructure — Fire Hydrants (3)](https://gis.eugene-or.gov/arcgis/rest/services/PWE/MiscInfra/MapServer/3) |
| `bike_lanes.geojson` | [Transportation — Bikeways Built (19)](https://gis.eugene-or.gov/arcgis/rest/services/PWE/Transportation/MapServer/19) |

The refresh script requests WGS84 GeoJSON and limits each layer to 1,000 features for a manageable prototype cache. These files are demonstration extracts, not authoritative operational datasets. Source schemas remain visible in the cache; the backend normalizes the fields exposed to the frontend.

Refresh and validate:

```bash
python scripts/fetch_eugene_data.py
python scripts/validate_geojson.py
```

Set `EUGENE_CACHE_ONLY=true` to exercise the no-network path. Each default service URL can be overridden with `EUGENE_ROADS_URL`, `EUGENE_SIDEWALK_RAMPS_URL`, `EUGENE_HYDRANTS_URL`, or `EUGENE_BIKE_LANES_URL`. A failed request leaves the existing cache unchanged.
