"""Calibration helpers. Fit only on a prior window; never on the reported test window."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ReliabilityBin:
    lower: float
    upper: float
    mean_predicted: float
    mean_actual: float
    count: int


def expected_calibration_error(
    actual_binary: Sequence[float],
    probabilities: Sequence[float],
    *,
    bins: int = 10,
) -> float:
    if len(actual_binary) != len(probabilities) or not actual_binary:
        raise ValueError("calibration inputs must be non-empty and equal length")
    if bins < 2:
        raise ValueError("bins must be >= 2")
    if any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("probabilities must be in [0, 1]")
    counts = [0] * bins
    pred_sum = [0.0] * bins
    actual_sum = [0.0] * bins
    n = len(probabilities)
    for y, p in zip(actual_binary, probabilities):
        idx = min(bins - 1, int(p * bins))
        counts[idx] += 1
        pred_sum[idx] += p
        actual_sum[idx] += float(y)
    ece = 0.0
    for i, count in enumerate(counts):
        if count == 0:
            continue
        ece += (count / n) * abs(pred_sum[i] / count - actual_sum[i] / count)
    return ece


def reliability_diagram(
    actual_binary: Sequence[float],
    probabilities: Sequence[float],
    *,
    bins: int = 10,
) -> list[ReliabilityBin]:
    ece_ok = expected_calibration_error(actual_binary, probabilities, bins=bins)
    _ = ece_ok
    out: list[ReliabilityBin] = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        ys = [float(y) for y, p in zip(actual_binary, probabilities) if lo <= p < hi or (i == bins - 1 and p == 1)]
        ps = [float(p) for p in probabilities if lo <= p < hi or (i == bins - 1 and p == 1)]
        if not ys:
            continue
        out.append(
            ReliabilityBin(
                lower=lo,
                upper=hi,
                mean_predicted=sum(ps) / len(ps),
                mean_actual=sum(ys) / len(ys),
                count=len(ys),
            )
        )
    return out


def interval_coverage(actual: Sequence[float], lower: Sequence[float], upper: Sequence[float]) -> float:
    if len(actual) != len(lower) or len(actual) != len(upper) or not actual:
        raise ValueError("interval inputs must be non-empty and equal length")
    return sum(float(lo <= x <= hi) for x, lo, hi in zip(actual, lower, upper)) / len(actual)
