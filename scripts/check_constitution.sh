#!/usr/bin/env bash
set -euo pipefail
EXPECTED_BLOB="918967e58543aa16df52585408efdccbc683c1a2"
ACTUAL_BLOB="$(git hash-object CONSTITUTION.md)"
if [ "$ACTUAL_BLOB" != "$EXPECTED_BLOB" ]; then
  echo "CONSTITUTION.md changed. Expected git blob $EXPECTED_BLOB, got $ACTUAL_BLOB" >&2
  exit 1
fi
echo "Constitution integrity OK: $ACTUAL_BLOB"
