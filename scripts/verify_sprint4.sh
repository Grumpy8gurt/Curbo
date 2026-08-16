#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Sprint 4 verification now delegates to the complete Sprint 5 checks."
exec "${SCRIPT_DIR}/verify_sprint5.sh"
