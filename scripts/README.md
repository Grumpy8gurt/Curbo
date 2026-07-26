# Scripts

This folder is for lightweight developer and bootstrap scripts shared across the monorepo. Keep scripts practical, documented, and safe for local development.

- `fetch_eugene_data.py`: refreshes configured public ArcGIS layers while preserving the committed cache on network failure.
- `validate_geojson.py`: validates every GeoJSON file under `data/eugene/` and `data/sample/`.
- `setup.sh`: starts the local PostGIS dependency.
