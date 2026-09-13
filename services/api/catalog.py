"""Read-only catalog of evaluation gates and model roles. No invented scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _entries_dir(root: Path | None = None) -> Path:
    return (root or REPO_ROOT) / "benchmarks" / "registry" / "entries"


def list_benchmarks(root: Path | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    directory = _entries_dir(root)
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            window = raw.get("time_range") if isinstance(raw.get("time_range"), dict) else {}
            metrics: list[str] = []
            for item in raw.get("metrics") or []:
                if isinstance(item, dict) and item.get("id"):
                    metrics.append(str(item["id"]))
                elif isinstance(item, str):
                    metrics.append(item)
            policy = raw.get("validation_policy") if isinstance(raw.get("validation_policy"), dict) else {}
            rows.append(
                {
                    "id": raw.get("id"),
                    "title": raw.get("title"),
                    "status": raw.get("status"),
                    "kind": raw.get("kind"),
                    "dataset_id": raw.get("dataset_id"),
                    "dataset_ref": raw.get("dataset_ref"),
                    "sealed": bool(window.get("sealed")),
                    "window_start": window.get("start"),
                    "window_end": window.get("end"),
                    "baseline_ids": list(raw.get("baseline_ids") or []),
                    "metric_ids": metrics,
                    "validation": policy.get("method"),
                    "random_shuffle_allowed": policy.get("random_shuffle_allowed"),
                    "notes": raw.get("notes") or raw.get("purpose"),
                }
            )
    return {
        "available": True,
        "promotion_allowed": False,
        "execution_enabled": False,
        "note": (
            "Registry names evaluation gates. Draft entries have no sealed window and no scores. "
            "This payload does not invent ECE, Brier, or MAE."
        ),
        "entries": rows,
    }


def list_models() -> dict[str, Any]:
    return {
        "available": True,
        "promotion_allowed": False,
        "execution_enabled": False,
        "feature_schema": "avax.features.mtf.v1",
        "incumbent": {
            "model_id": "baseline.drift20",
            "role": "live_journal",
            "promotion_allowed": False,
            "notes": (
                "Live and shadow-journal catch-up emit this point path. "
                "It is the named baseline, not a claimed champion."
            ),
        },
        "research": [
            {
                "model_id": "freqai.quantiles.research.v1",
                "role": "research_quantiles",
                "promotion_allowed": False,
                "notes": (
                    "Journaled q10/q50/q90 envelope when history exists. "
                    "Fixture walk-forward q50 MAE does not beat drift20. Not a promotion."
                ),
            },
            {
                "model_id": "empirical_signed_base_rate.v1",
                "role": "research_probability",
                "promotion_allowed": False,
                "notes": (
                    "P(close above origin) when enough matured train origins exist. "
                    "Null stays null. Not a fabricated confidence percentage."
                ),
            },
            {
                "model_id": "baseline.htf_regime_drift.v1",
                "role": "research_htf_gate",
                "promotion_allowed": False,
                "notes": (
                    "Gates 5m drift20 by three closed 4h closes. Not journaled live. "
                    "A lower fixture MAE is not a promotion."
                ),
            },
        ],
        "note": "Challengers stay research until a Watcher-accepted sealed walk-forward says otherwise.",
    }
