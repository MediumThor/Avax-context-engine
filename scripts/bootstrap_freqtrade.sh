#!/usr/bin/env bash
# Clone the complete pinned Freqtrade repository. Do not fork. Do not sparse-checkout.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN_FILE="$ROOT/adapters/freqtrade/pin.json"
DEST="${FREQTRADE_VENDOR_DIR:-$ROOT/vendor/freqtrade}"
REPO="https://github.com/freqtrade/freqtrade.git"
PIN="c064be5325ad6941a2789add795434e6a13dffe9"
LICENSE_ID="GPL-3.0"

if [[ -f "$PIN_FILE" ]]; then
  PIN="$(python3 -c "import json; print(json.load(open('$PIN_FILE'))['commit'])")"
  REPO="$(python3 -c "import json; print(json.load(open('$PIN_FILE'))['repo'])")"
  LICENSE_ID="$(python3 -c "import json; print(json.load(open('$PIN_FILE'))['license'])")"
fi

if [[ "$PIN" != "c064be5325ad6941a2789add795434e6a13dffe9" ]]; then
  echo "error: refusing to bootstrap unpinned commit $PIN" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"

if [[ ! -d "$DEST/.git" ]]; then
  # Complete clone: no --depth, no --filter, no sparse-checkout.
  git clone "$REPO" "$DEST"
fi

if git -C "$DEST" config --get core.sparseCheckout 2>/dev/null | grep -qi true; then
  echo "error: sparse checkout is not a complete upstream clone" >&2
  exit 1
fi

git -C "$DEST" fetch --all --tags --prune
git -C "$DEST" checkout --detach "$PIN"
HEAD="$(git -C "$DEST" rev-parse HEAD)"
if [[ "$HEAD" != "$PIN" ]]; then
  echo "error: checkout $HEAD does not match pin $PIN" >&2
  exit 1
fi

python3 - "$ROOT" "$DEST" "$PIN" "$LICENSE_ID" "$REPO" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from adapters.freqtrade.bootstrap import record_upstream_manifest

payload = record_upstream_manifest(
    Path(sys.argv[2]),
    commit=sys.argv[3],
    license_id=sys.argv[4],
    repo=sys.argv[5],
)
print(
    "Freqtrade pinned at {commit} license={license} license_file={license_file}".format(
        **payload
    )
)
PY
