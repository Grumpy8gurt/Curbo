#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: CONFIRM_CURBO_RESTORE=YES DATABASE_URL=... $0 <backup.dump>" >&2
  exit 1
fi
if [[ "${CONFIRM_CURBO_RESTORE:-}" != "YES" ]]; then
  echo "Set CONFIRM_CURBO_RESTORE=YES to confirm this destructive restore." >&2
  exit 1
fi
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required." >&2
  exit 1
fi

backup_path="$1"
if [[ ! -f "${backup_path}" ]]; then
  echo "Backup file not found: ${backup_path}" >&2
  exit 1
fi
if [[ -f "${backup_path}.sha256" ]]; then
  shasum -a 256 -c "${backup_path}.sha256"
fi

pg_restore --clean --if-exists --no-owner --no-acl --dbname="${DATABASE_URL}" "${backup_path}"
echo "Restore completed. Run application smoke tests before accepting traffic."
