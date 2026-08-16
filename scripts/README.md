# Scripts

This folder is for lightweight developer and bootstrap scripts shared across the monorepo. Keep scripts practical, documented, and safe for local development.

- `fetch_eugene_data.py`: refreshes configured public ArcGIS layers while preserving the committed cache on network failure; use `--layer roads` for a selective refresh.
- `backup_postgres.sh`: creates a restricted PostgreSQL custom-format dump and checksum.
- `restore_postgres.sh`: verifies and restores one dump after explicit destructive confirmation.
- `validate_geojson.py`: validates every GeoJSON file under `data/eugene/` and `data/sample/`.
- `setup.sh`: starts the local PostGIS dependency.
- `verify_sprint5.sh`: runs backend/frontend tests, Python and JavaScript
  dependency audits, the production build and bundle budget, GeoJSON
  validation, a migration round trip, and Docker Compose validation. Set
  `PYTHON_BIN=/absolute/path/to/python` to choose a specific environment.
- `verify_sprint4.sh`: preserved compatibility wrapper that delegates to the
  complete Sprint 5 verification script.
