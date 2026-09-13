"""Walk-forward scores for the live empirical P(up) and residual interval.

Uses only origins whose h-step outcome is still in the future at t.
Does not fit FreqAI. Does not promote. Does not shuffle.
"""

from __future__ import annotations

import math
from statistics import mean
from typing import Any, Sequence

from packages.evaluator.calibration import expected_calibration_error
from packages.evaluator.metrics import brier_score, interval_coverage
from packages.models.direction_cal import CALIBRATION_REF, empirical_signed_p

MIN_BRIER = 8
MIN_ECE = 15
MIN_COVERAGE = 8
INTERVAL_REF = "empirical_residual_vs_drift20.v1"


def _log_ret(later: float, now: float) -> float:
    return math.log(later / now)


def _drift20(closes: Sequence[float]) -> float:
    if len(closes) < 21:
        return 0.0
    past = [_log_ret(closes[j], closes[j - 1]) for j in range(len(closes) - 19, len(closes))]
    return mean(past)


def _quantile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile of empty series")
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def walk_forward_probabilities(
    candles: Sequence[Any],
    *,
    horizons: int = 10,
    min_history: int = 80,
    step: int = 15,
    as_of=None,
) -> dict[str, Any]:
    """Score empirical_signed_base_rate.v1 and residual q10–q90 on later-known closes."""
    if horizons < 1 or step < 1 or min_history < 21:
        raise ValueError("invalid walk-forward parameters")
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    if as_of is not None:
        closed = [c for c in closed if c.close_time() <= as_of]
    last = len(closed) - horizons
    origins = list(range(min_history - 1, last, step))
    drift_at = {s: _drift20([float(c.close) for c in closed[: s + 1]]) for s in origins}
    per_h: dict[int, dict[str, list[float]]] = {
        h: {"y": [], "p": [], "actual": [], "q10": [], "q90": []} for h in range(1, horizons + 1)
    }
    for t in origins:
        origin_close = float(closed[t].close)
        if origin_close <= 0:
            continue
        for h in range(1, horizons + 1):
            later = float(closed[t + h].close)
            if later <= 0:
                continue
            actual = _log_ret(later, origin_close)
            prior_actual: list[float] = []
            prior_score: list[float] = []
            for s in origins:
                if s >= t or s + h > t:
                    continue
                earlier = float(closed[s].close)
                known = float(closed[s + h].close)
                if earlier <= 0 or known <= 0:
                    continue
                prior_actual.append(_log_ret(known, earlier))
                prior_score.append(drift_at[s] * h)
            current_score = drift_at[t] * h
            p_up = empirical_signed_p(prior_actual, prior_score, current_score)
            if p_up is not None:
                per_h[h]["p"].append(p_up)
                per_h[h]["y"].append(1.0 if actual > 0 else 0.0)
            residuals = [a - d for a, d in zip(prior_actual, prior_score)]
            if len(residuals) >= MIN_COVERAGE:
                per_h[h]["actual"].append(actual)
                per_h[h]["q10"].append(current_score + _quantile(residuals, 0.1))
                per_h[h]["q90"].append(current_score + _quantile(residuals, 0.9))

    horizons_out: dict[str, Any] = {}
    for h in range(1, horizons + 1):
        series = per_h[h]
        n_p = len(series["p"])
        n_iv = len(series["actual"])
        brier = brier_score(series["y"], series["p"]) if n_p >= MIN_BRIER else None
        ece = expected_calibration_error(series["y"], series["p"], bins=5) if n_p >= MIN_ECE else None
        coverage = (
            interval_coverage(series["actual"], series["q10"], series["q90"])
            if n_iv >= MIN_COVERAGE
            else None
        )
        horizons_out[str(h)] = {
            "probability": {
                "sample_count": n_p,
                "brier": brier,
                "ece": ece,
                "calibration_ref": CALIBRATION_REF,
                "min_brier": MIN_BRIER,
                "min_ece": MIN_ECE,
                "note": "Walk-forward Brier/ECE of empirical signed P(up). Not a FreqAI promotion claim.",
            },
            "interval": {
                "sample_count": n_iv,
                "coverage": coverage,
                "interval": "q10-q90",
                "calibration_ref": INTERVAL_REF,
                "note": "Empirical residual-vs-drift20 hit rate. Not ECE and not a promotion claim.",
            },
        }

    return {
        "validation": "walk_forward",
        "calibration_ref": CALIBRATION_REF,
        "interval_ref": INTERVAL_REF,
        "promotion_allowed": False,
        "freqai_beats_baselines": None,
        "min_history": min_history,
        "step": step,
        "horizons": horizons_out,
    }
