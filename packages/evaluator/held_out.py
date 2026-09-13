"""Chronological held-out calibration. Never scores fixture data as live ECE."""

from __future__ import annotations

from typing import Any, Sequence

from packages.evaluator.calibration import expected_calibration_error

MIN_ECE = 15
HELD_OUT_FRACTION = 0.4
LIVE_CANDLE_SOURCES = frozenset({"binance-vision"})
FIXTURE_CANDLE_SOURCES = frozenset({"fixture"})


def is_live_candle_source(source: str | None) -> bool:
    return (source or "") in LIVE_CANDLE_SOURCES


def row_eligible_for_live_ece(payload_source: str | None, report_source: str | None) -> bool:
    """Fixture-tagged rows never enter live ECE. Untagged rows inherit the caller source."""
    if (report_source or "") in FIXTURE_CANDLE_SOURCES:
        return False
    if (payload_source or "") in FIXTURE_CANDLE_SOURCES:
        return False
    return is_live_candle_source(payload_source or report_source)


def held_out_start_index(n: int, fraction: float = HELD_OUT_FRACTION) -> int:
    """First index of the later chronological slice. Discovery window is [0, start)."""
    if n < 2:
        return n
    start = int(n * (1.0 - fraction))
    return min(max(start, 1), n - 1)


def held_out_ece(
    actual_binary: Sequence[float],
    probabilities: Sequence[float],
    *,
    report_source: str | None,
    bins: int = 5,
    min_ece: int = MIN_ECE,
    fraction: float = HELD_OUT_FRACTION,
) -> dict[str, Any]:
    """ECE on the later chronological slice only. Null when fixture or n is small."""
    if len(actual_binary) != len(probabilities):
        raise ValueError("held-out ECE inputs must be equal length")
    meta: dict[str, Any] = {
        "ece": None,
        "sample_count": len(actual_binary),
        "held_out_sample_count": 0,
        "validation": "chronological_held_out",
        "gate": "live_non_fixture",
        "reason": None,
        "promotion_allowed": False,
        "held_out_fraction": fraction,
        "min_ece": min_ece,
    }
    if not is_live_candle_source(report_source):
        meta["reason"] = "requires-live-non-fixture"
        return meta
    n = len(actual_binary)
    if n == 0:
        meta["reason"] = "insufficient-held-out"
        return meta
    start = held_out_start_index(n, fraction)
    y_h = list(actual_binary[start:])
    p_h = list(probabilities[start:])
    meta["held_out_sample_count"] = len(y_h)
    if len(y_h) < min_ece:
        meta["reason"] = "insufficient-held-out"
        return meta
    meta["ece"] = expected_calibration_error(y_h, p_h, bins=bins)
    return meta
