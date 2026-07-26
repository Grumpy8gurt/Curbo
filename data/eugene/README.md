# City of Eugene GIS Cache

This directory contains the local GeoJSON cache used by CURBO Sprint 3. The files are downloaded from public, API-key-free City of Eugene ArcGIS REST layers and retained in the repository so the demo does not require network access.

| CURBO layer | City service layer |
|---|---|
| `roads.geojson` | [Eugene Street Lines](https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugStLines/FeatureServer/0) |
| `sidewalk_ramps.geojson` | [Eugene Sidewalk Ramps](https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugSidewalkRamps/FeatureServer/0) |
| `hydrants.geojson` | [Eugene Fire Hydrants](https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugHydrants/FeatureServer/0) |
| `bike_lanes.geojson` | [Eugene Bikeways](https://services3.arcgis.com/F7NiRLGNbA2hh7gE/arcgis/rest/services/EugBikeways/FeatureServer/0) |

The committed files are 400-feature demonstration extracts, not authoritative operational datasets. The refresh script requests WGS84 GeoJSON and paginates each public service in 2,000-feature pages so a deliberate refresh can retrieve the complete available layer. Source schemas remain visible in the cache; the backend normalizes the fields exposed to the frontend.

Refresh and validate:

```bash
python scripts/fetch_eugene_data.py
python scripts/validate_geojson.py
```

Set `EUGENE_CACHE_ONLY=true` to exercise the no-network path. Each default service URL can be overridden with `EUGENE_ROADS_URL`, `EUGENE_SIDEWALK_RAMPS_URL`, `EUGENE_HYDRANTS_URL`, or `EUGENE_BIKE_LANES_URL`. A failed request leaves the existing cache unchanged.
