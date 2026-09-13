"""Helpers for cloning/pinning Freqtrade without forking it."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.freqtrade.constants import (
    PINNED_COMMIT,
    UPSTREAM_LICENSE,
    UPSTREAM_REPO,
    VENDOR_MANIFEST_NAME,
    VENDOR_RELATIVE,
)
from adapters.freqtrade.safety import load_pin


def vendor_dir(repo_root: Path) -> Path:
    return repo_root / VENDOR_RELATIVE


def detect_license_file(vendor: Path) -> Path | None:
    for name in ("LICENSE", "LICENSE.md", "COPYING"):
        candidate = vendor / name
        if candidate.is_file():
            return candidate
    return None


def record_upstream_manifest(
    vendor: Path,
    *,
    commit: str | None = None,
    license_id: str = UPSTREAM_LICENSE,
    repo: str = UPSTREAM_REPO,
) -> dict[str, Any]:
    """Write a generated license/pin record next to the cloned upstream tree."""
    pin = load_pin()
    expected = commit or pin["commit"]
    if expected != PINNED_COMMIT:
        raise ValueError(f"refusing to record non-pinned commit {expected}")
    license_file = detect_license_file(vendor)
    header = ""
    if license_file is not None:
        header = license_file.read_text(encoding="utf-8", errors="replace").splitlines()[:2]
        header = "\n".join(header)
    payload = {
        "repo": repo,
        "commit": expected,
        "license": license_id,
        "license_file": None if license_file is None else license_file.name,
        "license_header": header,
        "fork": False,
        "complete_clone": True,
        "copied_into_packages": False,
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    vendor.mkdir(parents=True, exist_ok=True)
    destination = vendor / VENDOR_MANIFEST_NAME
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
