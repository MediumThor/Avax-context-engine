"""Leakage-safe empirical P(close > origin).

Uses only origins whose outcomes are already known at T. This is a signed
base-rate calibrator, not a claim that FreqAI beats baselines.
"""

from __future__ import annotations

from typing import Sequence

CALIBRATION_REF = "empirical_signed_base_rate.v1"
MIN_BUCKET = 8


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
