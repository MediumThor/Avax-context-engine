"""Leakage-safe empirical P(close > origin).

Uses only origins whose outcomes are already known at T. This is a signed
base-rate calibrator, not a claim that FreqAI beats baselines.
"""

from __future__ import annotations

import math
from statistics import mean
from typing import Any, Sequence

CALIBRATION_REF = "empirical_signed_base_rate.v1"
MIN_BUCKET = 8


def _log_ret(later: float, now: float) -> float:
    return math.log(later / now)


def _drift20(closes: Sequence[float]) -> float:
    if len(closes) < 21:
        return 0.0
    past = [_log_ret(closes[j], closes[j - 1]) for j in range(len(closes) - 19, len(closes))]
    return mean(past)


def empirical_signed_p(
    targets: Sequence[float],
    scores: Sequence[float],
    current_score: float,
    *,
    min_bucket: int = MIN_BUCKET,
) -> float | None:
    """P(target > 0) in the same sign bucket as current_score.

    Flat scores fall back to the unconditional base rate. Returns None when
    the chosen bucket has fewer than ``min_bucket`` matured origins.
    """
    if len(targets) != len(scores) or not targets:
        return None
    if current_score > 0:
        ys = [1.0 if t > 0 else 0.0 for t, s in zip(targets, scores) if s > 0]
    elif current_score < 0:
        ys = [1.0 if t > 0 else 0.0 for t, s in zip(targets, scores) if s < 0]
    else:
        ys = [1.0 if t > 0 else 0.0 for t in targets]
    if len(ys) < min_bucket:
        return None
    return sum(ys) / len(ys)


def empirical_p_by_horizon(
    candles: Sequence[Any],
    *,
    horizons: int = 10,
    min_bucket: int = MIN_BUCKET,
) -> dict[int, float | None]:
    """P(close > origin) at the last closed bar, using only earlier matured pairs.

    Does not change the drift20 point path. Returns None per horizon when the
    sign bucket is smaller than ``min_bucket``.
    """
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    out: dict[int, float | None] = {h: None for h in range(1, horizons + 1)}
    if len(closed) < 21 + min_bucket:
        return out
    closes = [float(c.close) for c in closed]
    drift_at = [0.0] * len(closes)
    for i in range(20, len(closes)):
        drift_at[i] = _drift20(closes[: i + 1])
    t = len(closes) - 1
    current = drift_at[t]
    for h in range(1, horizons + 1):
        last_s = t - h
        if last_s < 20:
            continue
        prior_actual: list[float] = []
        prior_score: list[float] = []
        for s in range(20, last_s + 1):
            earlier = closes[s]
            known = closes[s + h]
            if earlier <= 0 or known <= 0:
                continue
            prior_actual.append(_log_ret(known, earlier))
            prior_score.append(drift_at[s] * h)
        out[h] = empirical_signed_p(prior_actual, prior_score, current * h, min_bucket=min_bucket)
    return out


def attach_empirical_signed_p(payload: dict[str, Any], candles: Sequence[Any]) -> dict[str, Any]:
    """Fill null ``p_close_above_origin`` from the signed base rate. Never overwrite."""
    rows = payload.get("horizons") or []
    if not rows:
        return payload
    needed = any(row.get("p_close_above_origin") is None and "h" in row for row in rows)
    if not needed:
        return payload
    by_h = empirical_p_by_horizon(candles, horizons=max(int(row["h"]) for row in rows if "h" in row))
    filled = False
    for row in rows:
        if row.get("p_close_above_origin") is not None or "h" not in row:
            continue
        p = by_h.get(int(row["h"]))
        if p is None:
            continue
        row["p_close_above_origin"] = p
        row["confidence_source"] = CALIBRATION_REF
        filled = True
    if filled:
        payload["calibration_ref"] = CALIBRATION_REF
        payload["promotion_allowed"] = False
        note = (
            "Empirical signed P(up) attached when the bucket is large enough. "
            "Not a promotion."
        )
        existing = str(payload.get("notes") or "").strip()
        if note not in existing:
            payload["notes"] = f"{existing} {note}".strip()
    return payload
