"""Leakage-safe ATR/zigzag confirmed pivots (second method).

Window extrema remain in ``structure.confirmed_pivots``. This module does not
replace that function.

A pivot's ``time`` / ``index`` is the extreme candle. ``known_at`` /
``known_at_index`` is the first *closed* candle at which price reversed by
``atr_multiple * ATR``. The pivot is unavailable before ``known_at``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from .indicators import atr
from .models import Candle, Pivot

DEFAULT_ATR_PERIOD = 14
DEFAULT_ATR_MULTIPLE = 2.0

_Direction = Literal["up", "down"]


def pivots_known_as_of(pivots: list[Pivot], as_of: datetime) -> list[Pivot]:
    """Return pivots that were already confirmed by ``as_of`` (inclusive)."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return [pivot for pivot in pivots if pivot.known_at <= as_of]


def atr_zigzag_pivots(
    candles: list[Candle],
    atr_period: int = DEFAULT_ATR_PERIOD,
    atr_multiple: float = DEFAULT_ATR_MULTIPLE,
    as_of: datetime | None = None,
) -> list[Pivot]:
    """Confirmed ATR/zigzag pivots using only information known at each bar.

    Parameters
    ----------
    candles:
        Chronological candles. Unclosed bars are ignored. If ``as_of`` is set,
        bars with ``open_time > as_of`` are ignored so future OHLC cannot
        confirm or rewrite earlier pivots.
    atr_period:
        Wilder ATR lookback. ATR at bar i uses candles ``0..i`` only.
    atr_multiple:
        Reversal size, in ATRs, required to confirm a candidate extreme.
    as_of:
        Optional inclusive cutoff. A pivot is returned only if its confirmation
        candle is at or before this timestamp.
    """
    if atr_period < 1:
        raise ValueError("atr_period must be >= 1")
    if atr_multiple <= 0:
        raise ValueError("atr_multiple must be > 0")
    if as_of is not None and as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    series = _closed_prefix(candles, as_of)
    if len(series) < 2:
        return []

    highs = [c.high for _, c in series]
    lows = [c.low for _, c in series]
    closes = [c.close for _, c in series]
    atrs = atr(highs, lows, closes, atr_period)

    start = next((i for i, value in enumerate(atrs) if value is not None), None)
    if start is None:
        return []

    out: list[Pivot] = []
    direction: _Direction | None = None
    hi_orig, hi_candle = series[start]
    lo_orig, lo_candle = series[start]
    hi_price, lo_price = hi_candle.high, lo_candle.low

    for i in range(start, len(series)):
        orig_i, candle = series[i]
        value = atrs[i]
        if value is None:
            continue
        threshold = value * atr_multiple

        if direction is None:
            if candle.high > hi_price:
                hi_orig, hi_price = orig_i, candle.high
            if candle.low < lo_price:
                lo_orig, lo_price = orig_i, candle.low
            pick = _first_confirmation(candle, hi_price, lo_price, hi_orig, lo_orig, threshold)
            if pick == "high":
                out.append(_pivot(candles, hi_orig, orig_i, "high"))
                direction = "down"
                lo_orig, lo_price = orig_i, candle.low
            elif pick == "low":
                out.append(_pivot(candles, lo_orig, orig_i, "low"))
                direction = "up"
                hi_orig, hi_price = orig_i, candle.high
            continue

        if direction == "up":
            if candle.high > hi_price:
                hi_orig, hi_price = orig_i, candle.high
            if threshold > 0 and hi_price - candle.low >= threshold:
                out.append(_pivot(candles, hi_orig, orig_i, "high"))
                direction = "down"
                lo_orig, lo_price = orig_i, candle.low
        else:
            if candle.low < lo_price:
                lo_orig, lo_price = orig_i, candle.low
            if threshold > 0 and candle.high - lo_price >= threshold:
                out.append(_pivot(candles, lo_orig, orig_i, "low"))
                direction = "up"
                hi_orig, hi_price = orig_i, candle.high

    return out


def _closed_prefix(candles: list[Candle], as_of: datetime | None) -> list[tuple[int, Candle]]:
    series: list[tuple[int, Candle]] = []
    last_time: datetime | None = None
    for index, candle in enumerate(candles):
        if not candle.is_closed:
            continue
        if as_of is not None and candle.open_time > as_of:
            continue
        if last_time is not None and candle.open_time <= last_time:
            raise ValueError("candles must be strictly increasing by open_time")
        last_time = candle.open_time
        series.append((index, candle))
    return series


def _first_confirmation(
    candle: Candle,
    hi_price: float,
    lo_price: float,
    hi_orig: int,
    lo_orig: int,
    threshold: float,
) -> Literal["high", "low"] | None:
    if threshold <= 0:
        return None
    high_ret = hi_price - candle.low
    low_ret = candle.high - lo_price
    confirm_high = high_ret >= threshold
    confirm_low = low_ret >= threshold
    if confirm_high and confirm_low:
        if high_ret > low_ret:
            return "high"
        if low_ret > high_ret:
            return "low"
        return "high" if hi_orig <= lo_orig else "low"
    if confirm_high:
        return "high"
    if confirm_low:
        return "low"
    return None


def _pivot(candles: list[Candle], extreme_index: int, known_index: int, kind: Literal["high", "low"]) -> Pivot:
    extreme = candles[extreme_index]
    known = candles[known_index]
    price = extreme.high if kind == "high" else extreme.low
    return Pivot(
        index=extreme_index,
        known_at_index=known_index,
        time=extreme.open_time,
        known_at=known.open_time,
        price=price,
        kind=kind,
    )
