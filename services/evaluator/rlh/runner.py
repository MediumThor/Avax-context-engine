"""RLH fixture directory runner. Does not score ForecastPackage accuracy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.evaluator.rlh.metrics import score_trace


def run_fixture_dir(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    expected = json.loads((root / "expected_invariants.json").read_text())
    trace_path = root / "loop_trace.json"
    if not trace_path.exists():
        return {"fixture": root.name, "status": "invariants_only", "expected": expected}
    trace = json.loads(trace_path.read_text())
    parent = expected.get("parent_regime_after_failed_breakout")
    metrics = score_trace(trace, expected_parent_regime=parent)
    return {"fixture": root.name, "status": "scored", "expected": expected, "metrics": metrics}
