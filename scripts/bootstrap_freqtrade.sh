#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/vendor/freqtrade"
PIN="c064be5325ad6941a2789add795434e6a13dffe9"
mkdir -p "$ROOT/vendor"
if [ ! -d "$DEST/.git" ]; then
  git clone https://github.com/freqtrade/freqtrade.git "$DEST"
fi
git -C "$DEST" fetch --all --tags --prune
git -C "$DEST" checkout --detach "$PIN"
printf 'Freqtrade pinned at %s\n' "$(git -C "$DEST" rev-parse HEAD)"
