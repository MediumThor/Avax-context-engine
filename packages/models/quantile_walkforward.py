"""Chronological walk-forward of the research quantile challenger vs baselines.

Does not promote the challenger. Does not shuffle. Does not invent ECE.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from packages.evaluator.metrics import interval_coverage, mae, pinball_loss, rmse, signed_direction_accuracy
from packages.models.baselines import emit_baseline_forecast
from packages.models.freqai_quantiles import InsufficientHistory, emit_quantile_forecast

MODEL_ID = "freqai.quantiles.research.v1"
TARGET = "cumulative_log_return"


def _log_ret(later: float, now: float) -> float:
    return math.log(later / now)


def _row_by_h(horizons: Sequence[dict[str, Any]], h: int) -> dict[str, Any]:
    for row in horizons:
        if int(row["h"]) == h:
            return row
    raise KeyError(h)


def walk_forward_quantiles(
    candles: Sequence[Any],
    *,
    horizons: int = 10,
    min_history: int = 120,
    step: int = 20,
    lookback: int = 400,
    backend: str = "python",
    min_train: int = 30,
) -> dict[str, Any]:
    """Score q50 / q10–q90 against zero and drift20 on outcomes still in the future at t."""
    if horizons < 1 or step < 1 or lookback < 1 or min_history < 21:
        raise ValueError("invalid walk-forward parameters")
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    last = len(closed) - horizons
    collected: dict[str, dict[str, list[float]]] = {
        str(h): {"actual": [], "zero": [], "drift20": [], "q50": [], "q10": [], "q90": []}
        for h in range(1, horizons + 1)
    }
    origin_count = 0
    skipped = 0
    for t in range(min_history - 1, last, step):
        hist = closed[: t + 1]
        as_of = hist[-1].close_time()
        visible = [c for c in hist if c.close_time() <= as_of]
        window = visible[-lookback:] if len(visible) > lookback else list(visible)
        try:
            quantile = emit_quantile_forecast(window, as_of=as_of, backend=backend, min_train=min_train)
        except InsufficientHistory:
            skipped += 1
            continue
        baseline = emit_baseline_forecast(visible, horizons=horizons)
        origin_close = float(visible[-1].close)
        origin_count += 1
        for h in range(1, horizons + 1):
            actual = _log_ret(float(closed[t + h].close), origin_close)
            qrow = _row_by_h(quantile["horizons"], h)
            brow = _row_by_h(baseline["horizons"], h)
            key = str(h)
            collected[key]["actual"].append(actual)
            collected[key]["zero"].append(0.0)
            collected[key]["drift20"].append(float(brow["drift20_cum_log_return"]))
            collected[key]["q50"].append(float(qrow["q50_cum_log_return"]))
            collected[key]["q10"].append(float(qrow["q10_cum_log_return"]))
            collected[key]["q90"].append(float(qrow["q90_cum_log_return"]))

    horizons_out: dict[str, Any] = {}
    q50_beats = []
    for h, series in collected.items():
        actual = series["actual"]
        if not actual:
            horizons_out[h] = {"sample_count": 0}
            q50_beats.append(False)
            continue
        q50_mae = mae(actual, series["q50"])
        drift_mae = mae(actual, series["drift20"])
        block = {
            "sample_count": len(actual),
            "target": TARGET,
            "validation": "walk_forward",
            "zero": {"mae": mae(actual, series["zero"]), "rmse": rmse(actual, series["zero"])},
            "drift20": {
                "mae": drift_mae,
                "rmse": rmse(actual, series["drift20"]),
                "signed_direction": signed_direction_accuracy(actual, series["drift20"]),
            },
            "q50": {
                "mae": q50_mae,
                "rmse": rmse(actual, series["q50"]),
                "signed_direction": signed_direction_accuracy(actual, series["q50"]),
                "pinball_0_5": pinball_loss(actual, series["q50"], 0.5),
            },
            "q10_q90": {
                "coverage": interval_coverage(actual, series["q10"], series["q90"]),
                "pinball_q10": pinball_loss(actual, series["q10"], 0.1),
                "pinball_q90": pinball_loss(actual, series["q90"], 0.9),
                "note": "Empirical interval hit rate, not a calibrated ECE.",
            },
            "q50_mae_minus_drift20_mae": q50_mae - drift_mae,
        }
        horizons_out[h] = block
        q50_beats.append(q50_mae < drift_mae)

    beats = all(q50_beats) and origin_count > 0 and all(
        horizons_out[str(h)].get("sample_count", 0) > 0 for h in range(1, horizons + 1)
    )
    return {
        "validation": "walk_forward",
        "model_id": MODEL_ID,
        "baseline_refs": ["baseline.zero", "baseline.drift20"],
        "min_history": min_history,
        "step": step,
        "lookback": lookback,
        "backend": backend,
        "target": TARGET,
        "origin_count": origin_count,
        "skipped_insufficient_history": skipped,
        "horizons": horizons_out,
        "q50_mae_below_drift20_on_all_scored_horizons": beats if origin_count else None,
        "promotion_allowed": False,
        "freqai_beats_baselines": None,
        "notes": (
            "Research walk-forward only. A lower q50 MAE on this run is not a promotion. "
            "Coverage is an empirical hit rate, not ECE."
        ),
    }
