"""Research baseline: gate 5m drift20 by closed higher-timeframe direction.

Does not replace baseline.drift20. Does not emit live forecasts. Does not promote.
Uses only closed parent bars whose period end is known at the origin.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from packages.context_engine.engine import TIMEFRAMES
from packages.context_engine.models import Candle
from packages.context_engine.resample import resample_closed
from packages.evaluator.metrics import mae, rmse, signed_direction_accuracy
from packages.models.baselines import emit_baseline_forecast

MODEL_ID = "baseline.htf_regime_drift.v1"
PARENT_TF = "4h"
TARGET = "cumulative_log_return"


def _log_ret(later: float, now: float) -> float:
    return math.log(later / now)


def parent_regime(candles_5m: Sequence[Candle], *, parent_tf: str = PARENT_TF) -> str:
    """Three consecutive closed parent closes. Incomplete buckets are dropped."""
    minutes = TIMEFRAMES[parent_tf]
    bars = resample_closed(list(candles_5m), minutes, parent_tf)
    if len(bars) < 3:
        return "neutral"
    older, mid, last = bars[-3].close, bars[-2].close, bars[-1].close
    if last < mid < older:
        return "bearish"
    if last > mid > older:
        return "bullish"
    return "neutral"


def _gate_step(drift: float, regime: str) -> float:
    if regime == "bearish":
        return min(drift, 0.0)
    if regime == "bullish":
        return max(drift, 0.0)
    return drift


def emit_htf_regime_forecast(
    candles: Sequence[Candle],
    horizons: int = 10,
    *,
    parent_tf: str = PARENT_TF,
) -> dict[str, Any]:
    """Point-in-time gated drift. Caller must already truncate to as_of."""
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    baseline = emit_baseline_forecast(closed, horizons)
    drift = float(baseline["horizons"][0]["drift20_cum_log_return"])
    regime = parent_regime(closed, parent_tf=parent_tf)
    step = _gate_step(drift, regime)
    horizons_out = []
    for row in baseline["horizons"]:
        h = int(row["h"])
        horizons_out.append(
            {
                "h": h,
                "zero_cum_log_return": 0.0,
                "drift20_cum_log_return": float(row["drift20_cum_log_return"]),
                "htf_regime_cum_log_return": step * h,
                "expected_cum_log_return": step * h,
                "parent_regime": regime,
                "p_close_above_origin": None,
                "confidence_source": "insufficient-data",
            }
        )
    origin = closed[-1]
    return {
        "model_id": MODEL_ID,
        "baseline_refs": ["baseline.zero", "baseline.drift20"],
        "parent_tf": parent_tf,
        "parent_regime": regime,
        "symbol": origin.symbol,
        "forecasted_at": origin.close_time().isoformat(),
        "origin_close": origin.close,
        "origin_open_time": origin.open_time.isoformat(),
        "horizons": horizons_out,
        "promotion_allowed": False,
        "confidence_source": "insufficient-data",
        "notes": (
            "Research HTF gate on drift20. A 5m bounce does not overwrite a "
            "bearish 4h sequence. No calibrated probability. Not a promotion."
        ),
    }


def walk_forward_htf_regime(
    candles: Sequence[Candle],
    *,
    horizons: int = 10,
    min_history: int = 200,
    step: int = 20,
    parent_tf: str = PARENT_TF,
) -> dict[str, Any]:
    """Score gated drift vs drift20 on outcomes still in the future at t."""
    if horizons < 1 or step < 1 or min_history < 21:
        raise ValueError("invalid walk-forward parameters")
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    last = len(closed) - horizons
    collected: dict[str, dict[str, list[float]]] = {
        str(h): {"actual": [], "zero": [], "drift20": [], "htf": []} for h in range(1, horizons + 1)
    }
    origin_count = 0
    for t in range(min_history - 1, last, step):
        hist = closed[: t + 1]
        forecast = emit_htf_regime_forecast(hist, horizons, parent_tf=parent_tf)
        origin_close = float(hist[-1].close)
        origin_count += 1
        for row in forecast["horizons"]:
            h = int(row["h"])
            actual = _log_ret(float(closed[t + h].close), origin_close)
            key = str(h)
            collected[key]["actual"].append(actual)
            collected[key]["zero"].append(0.0)
            collected[key]["drift20"].append(float(row["drift20_cum_log_return"]))
            collected[key]["htf"].append(float(row["htf_regime_cum_log_return"]))

    horizons_out: dict[str, Any] = {}
    beats = []
    for h, series in collected.items():
        actual = series["actual"]
        if not actual:
            horizons_out[h] = {"sample_count": 0}
            beats.append(False)
            continue
        htf_mae = mae(actual, series["htf"])
        drift_mae = mae(actual, series["drift20"])
        horizons_out[h] = {
            "sample_count": len(actual),
            "target": TARGET,
            "validation": "walk_forward",
            "zero": {"mae": mae(actual, series["zero"]), "rmse": rmse(actual, series["zero"])},
            "drift20": {
                "mae": drift_mae,
                "rmse": rmse(actual, series["drift20"]),
                "signed_direction": signed_direction_accuracy(actual, series["drift20"]),
            },
            "htf_regime": {
                "mae": htf_mae,
                "rmse": rmse(actual, series["htf"]),
                "signed_direction": signed_direction_accuracy(actual, series["htf"]),
            },
            "htf_mae_minus_drift20_mae": htf_mae - drift_mae,
        }
        beats.append(htf_mae < drift_mae)

    all_scored = origin_count > 0 and all(
        horizons_out[str(h)].get("sample_count", 0) > 0 for h in range(1, horizons + 1)
    )
    return {
        "validation": "walk_forward",
        "model_id": MODEL_ID,
        "baseline_refs": ["baseline.zero", "baseline.drift20"],
        "parent_tf": parent_tf,
        "min_history": min_history,
        "step": step,
        "target": TARGET,
        "origin_count": origin_count,
        "horizons": horizons_out,
        "htf_mae_below_drift20_on_all_scored_horizons": all(beats) if all_scored else None,
        "promotion_allowed": False,
        "notes": (
            "Research walk-forward only. A lower HTF-gated MAE on this run is not a promotion. "
            "5m relief must not overwrite a closed 4h decline."
        ),
    }
