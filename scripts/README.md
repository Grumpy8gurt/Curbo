# Scripts

This folder is for lightweight developer and bootstrap scripts shared across the monorepo. Keep scripts practical, documented, and safe for local development.

- `fetch_eugene_data.py`: refreshes configured public ArcGIS layers while preserving the committed cache on network failure; use `--layer roads` for a selective refresh.
- `validate_geojson.py`: validates every GeoJSON file under `data/eugene/` and `data/sample/`.
- `setup.sh`: starts the local PostGIS dependency.
- `verify_sprint4.sh`: runs backend and frontend tests, the production build,
  dependency audit, GeoJSON validation, and Docker Compose configuration when
  Docker is available. Set `PYTHON_BIN=/absolute/path/to/python` to choose a
  specific Python environment.
