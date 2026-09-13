"""RLH max_depth ablation — process metrics only, not forecast accuracy."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from services.evaluator.rlh.metrics import score_trace
from services.harness.loop import run_loop

DEFAULT_DEPTHS: tuple[int, ...] = (1, 2, 4, 8, 16)

NOTES = (
    "Depth ablation records loop process metrics at varying max_depth. "
    "Extra depth is NOT an accuracy claim and does not change ForecastPackage numeric heads. "
    "Do not use depth-ablation pass rates to promote harness versions."
)


def _forecast_snapshot(forecast: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(forecast))


def _row(trace: Mapping[str, Any], *, depth: int, expected_parent_regime: str | None) -> dict[str, Any]:
    halt = trace.get("halt") or {}
    kinds = [step.get("kind") for step in trace.get("steps") or []]
    metrics = score_trace(trace, expected_parent_regime=expected_parent_regime)
    return {
        "max_depth": depth,
        "halt_reason": halt.get("reason"),
        "depth_used": halt.get("depth_used"),
        "step_count": len(trace.get("steps") or []),
        "no_change_fired": "NO_CHANGE" in kinds,
        "encoder_memory_hash": trace.get("encoder_memory_hash"),
        "forecast_package_id": trace.get("forecast_package_id"),
        "process_metrics": metrics,
    }


def ablate_depths(
    memory: Mapping[str, Any],
    forecast: Mapping[str, Any],
    depths: tuple[int, ...] = DEFAULT_DEPTHS,
    *,
    expected_parent_regime: str | None = None,
    artifact_dir: str | Path | None = None,
    **run_loop_kwargs: Any,
) -> dict[str, Any]:
    """Run ``run_loop`` at each ``max_depth`` and record process-quality metrics only."""
    forecast_before = _forecast_snapshot(forecast)
    rows: list[dict[str, Any]] = []

    for depth in depths:
        trace = run_loop(memory=memory, forecast=forecast, max_depth=depth, **run_loop_kwargs)
        rows.append(_row(trace, depth=depth, expected_parent_regime=expected_parent_regime))

    if forecast_before != _forecast_snapshot(forecast):
        raise ValueError("forecast_package_mutated_during_ablation")

    report: dict[str, Any] = {
        "schema_version": "1",
        "as_of": memory.get("as_of"),
        "encoder_memory_id": memory.get("id"),
        "encoder_memory_hash": memory.get("content_hash"),
        "forecast_package_id": str(forecast.get("id") or memory.get("forecast_package_id")),
        "forecast_package_snapshot": forecast_before,
        "depths": list(depths),
        "rows": rows,
        "promotion_allowed": False,
        "notes": NOTES,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }

    if artifact_dir is not None:
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        stem = f"{memory.get('id', 'memory')}-{memory.get('as_of', 'unknown')}".replace(":", "")
        path = root / f"{stem}.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        report["artifact_path"] = str(path)

    return report
