from __future__ import annotations

import math
from statistics import mean

from packages.context_engine.models import Candle
from packages.evaluator.metrics import mae, rmse, signed_direction_accuracy


def _log_ret(later: float, now: float) -> float:
    return math.log(later / now)


def _drift20(closes: list[float]) -> float:
    if len(closes) < 21:
        return 0.0
    past = [_log_ret(closes[j], closes[j - 1]) for j in range(len(closes) - 19, len(closes))]
    return mean(past)


def emit_baseline_forecast(candles: list[Candle], horizons: int = 10) -> dict:
    """Point-in-time forecast using only the provided (already truncated) candles."""
    closed = [c for c in candles if c.is_closed]
    if len(closed) < 21:
        raise ValueError("Need at least 21 closed candles to emit a baseline forecast")
    closes = [c.close for c in closed]
    drift = _drift20(closes)
    origin = closed[-1]
    horizons_out = []
    for h in range(1, horizons + 1):
        horizons_out.append(
            {
                "h": h,
                "zero_cum_log_return": 0.0,
                "drift20_cum_log_return": drift * h,
                "expected_cum_log_return": drift * h,
                "p_close_above_origin": None,
                "confidence_source": "insufficient-data",
            }
        )
    return {
        "model_id": "baseline.drift20",
        "baseline_refs": ["baseline.zero", "baseline.drift20"],
        "symbol": origin.symbol,
        "forecasted_at": origin.close_time().isoformat(),
        "origin_close": origin.close,
        "origin_open_time": origin.open_time.isoformat(),
        "horizons": horizons_out,
        "confidence_source": "insufficient-data",
        "notes": "Expected path is trailing 20-bar drift. No calibrated probability is claimed.",
    }


def walk_forward_baselines(
    candles: list[Candle],
    horizons: int = 10,
    min_history: int = 80,
    step: int = 10,
) -> dict:
    """Score baselines only on outcomes that were still in the future at forecast time."""
    closed = [c for c in candles if c.is_closed]
    if len(closed) < min_history + horizons + 1:
        raise ValueError("Not enough candles for walk-forward baselines")
    closes = [c.close for c in closed]
    collected: dict[str, dict[str, list[float]]] = {
        str(h): {"actual": [], "zero": [], "drift20": []} for h in range(1, horizons + 1)
    }
    last = len(closed) - horizons
    for t in range(min_history, last, step):
        hist = closed[: t + 1]
        forecast = emit_baseline_forecast(hist, horizons)
        for item in forecast["horizons"]:
            h = item["h"]
            actual = _log_ret(closes[t + h], closes[t])
            key = str(h)
            collected[key]["actual"].append(actual)
            collected[key]["zero"].append(0.0)
            collected[key]["drift20"].append(item["drift20_cum_log_return"])
    horizons_out = {}
    for h, series in collected.items():
        actual = series["actual"]
        horizons_out[h] = {
            "sample_count": len(actual),
            "target": "cumulative_log_return",
            "validation": "walk_forward",
            "zero": {
                "mae": mae(actual, series["zero"]),
                "rmse": rmse(actual, series["zero"]),
                "signed_direction": signed_direction_accuracy(actual, series["zero"]),
            },
            "drift20": {
                "mae": mae(actual, series["drift20"]),
                "rmse": rmse(actual, series["drift20"]),
                "signed_direction": signed_direction_accuracy(actual, series["drift20"]),
            },
        }
    return {
        "validation": "walk_forward",
        "min_history": min_history,
        "step": step,
        "target": "cumulative_log_return",
        "horizons": horizons_out,
    }


def evaluate_baselines(candles: list[Candle], horizons: int = 10) -> dict:
    """In-sample helper retained for unit tests. Do not report as live accuracy."""
    if len(candles) < 300:
        raise ValueError("At least 300 candles required")
    closes = [c.close for c in candles]
    results = {}
    for h in range(1, horizons + 1):
        actual = [math.log(closes[i + h] / closes[i]) for i in range(len(closes) - h)][20:]
        zero = [0.0] * len(actual)
        drift = []
        for i in range(20, len(closes) - h):
            past = [math.log(closes[j] / closes[j - 1]) for j in range(i - 19, i + 1)]
            drift.append(mean(past) * h)
        results[str(h)] = {
            "zero": {"mae": mae(actual, zero), "rmse": rmse(actual, zero)},
            "drift20": {
                "mae": mae(actual, drift),
                "rmse": rmse(actual, drift),
                "signed_direction": signed_direction_accuracy(actual, drift),
            },
            "sample_count": len(actual),
        }
    return results
