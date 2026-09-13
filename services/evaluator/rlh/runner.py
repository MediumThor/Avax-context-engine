"""RLH fixture directory runner. Does not score ForecastPackage accuracy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from services.evaluator.rlh.metrics import score_trace

# expected_invariants keys that require a journaled LoopTrace to evaluate process metrics.
_SCORED_TRACE_KEYS = frozenset(
    {
        "parent_regime_after_failed_breakout",
        "relief_bounce_is_not_reversal",
        "invalidation_immutable",
        "challenge_required",
        "encode_check_first",
        "halt_required",
        "halt_reason",
        "halt_reason_allowed",
        "must_not_move_invalidation",
        "closed_or_respected_thesis",
        "parent_regime_preserved",
        "parent_regime",
        "child_regime_may_be_bullish",
        "interpretation_must_include_relief_not_reversal",
        "degraded",
        "no_confident_forecast_language",
        "confidence_source",
        "must_restate_ensemble_disagreement",
        "analog_search_refuses_known_at_after_as_of",
        "refused_tool_is_success",
        "leakage_probe_passed",
        "rebuild_policy",
        "live_hash_equals_replay_hash",
        "reveal_future",
        "no_uncalibrated_percent",
        "max_depth_not_required",
    }
)

REQUIRED_FIXTURES = (
    "avax-2026-09-failed-8",
    "no-change-5m",
    "stale-data",
    "invalidation-already-fired",
    "model-disagreement",
    "parent-child-split",
    "analog-cutoff",
    "replay-parity",
)


def requires_scored_trace(expected: Mapping[str, Any] | None) -> bool:
    if not expected:
        return False
    return bool(set(expected) & _SCORED_TRACE_KEYS)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def run_fixture_dir(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    expected = json.loads((root / "expected_invariants.json").read_text())
    manifest = _load_json(root / "manifest.json")
    trace_path = root / "loop_trace.json"
    needs_trace = requires_scored_trace(expected)

    if not trace_path.exists():
        status = "incomplete" if needs_trace else "invariants_only"
        result: dict[str, Any] = {
            "fixture": root.name,
            "status": status,
            "passed": False,
            "expected": expected,
        }
        if manifest is not None:
            result["manifest"] = manifest
        if needs_trace:
            result["blocking_reason"] = "loop_trace.json missing"
        return result

    trace = json.loads(trace_path.read_text())
    parent = expected.get("parent_regime_after_failed_breakout") or expected.get("parent_regime")
    metrics = score_trace(trace, expected_parent_regime=parent)
    return {
        "fixture": root.name,
        "status": "scored",
        "passed": bool(metrics.get("passed")),
        "expected": expected,
        "metrics": metrics,
        **({"manifest": manifest} if manifest is not None else {}),
    }
