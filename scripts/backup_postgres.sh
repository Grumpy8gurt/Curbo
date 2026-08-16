#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required." >&2
  exit 1
fi

backup_directory="${CURBO_BACKUP_DIR:-./backups}"
if [[ "${backup_directory}" == "/" ]]; then
  echo "Refusing to use / as the backup directory." >&2
  exit 1
fi

mkdir -p "${backup_directory}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="${backup_directory}/curbo-${timestamp}.dump"

umask 077
pg_dump --format=custom --no-owner --no-acl --file="${backup_path}" "${DATABASE_URL}"
shasum -a 256 "${backup_path}" > "${backup_path}.sha256"

echo "Backup created: ${backup_path}"
echo "Copy it to encrypted, versioned storage outside the application host."
