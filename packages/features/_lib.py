"""Fallback indicator/resample implementations.

These match ``packages.context_engine.indicators`` and
``packages.context_engine.resample`` so the assembler can run on main before
that package is present, and so reuse can be compared when it is.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import sqrt
from typing import Iterable

from .types import FeatureCandle


def ema(values: Iterable[float], span: int) -> list[float]:
    xs = list(values)
    if not xs:
        return []
    alpha = 2.0 / (span + 1.0)
    out = [float(xs[0])]
    for value in xs[1:]:
        out.append(alpha * float(value) + (1.0 - alpha) * out[-1])
    return out


def rsi(values: Iterable[float], period: int = 14) -> list[float | None]:
    xs = list(values)
    out: list[float | None] = [None] * len(xs)
    if len(xs) <= period:
        return out
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, period + 1):
        d = xs[i] - xs[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, len(xs)):
        d = xs[i] - xs[i - 1]
        gain = max(d, 0.0)
        loss = max(-d, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


def atr(
    highs: Iterable[float],
    lows: Iterable[float],
    closes: Iterable[float],
    period: int = 14,
) -> list[float | None]:
    h, l, c = list(highs), list(lows), list(closes)
    out: list[float | None] = [None] * len(c)
    if not c:
        return out
    trs = [h[0] - l[0]]
    for i in range(1, len(c)):
        trs.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    if len(trs) < period:
        return out
    current = sum(trs[:period]) / period
    out[period - 1] = current
    for i in range(period, len(trs)):
        current = (current * (period - 1) + trs[i]) / period
        out[i] = current
    return out


def realized_volatility(values: Iterable[float], window: int = 24) -> float | None:
    xs = list(values)
    if len(xs) < window + 1:
        return None
    returns = [(xs[i] / xs[i - 1]) - 1.0 for i in range(len(xs) - window, len(xs))]
    mean = sum(returns) / len(returns)
    variance = sum((x - mean) ** 2 for x in returns) / len(returns)
    return sqrt(variance)


def floor_time(dt: datetime, minutes: int) -> datetime:
    dt = dt.astimezone(timezone.utc)
    epoch_minutes = int(dt.timestamp() // 60)
    floored = epoch_minutes - (epoch_minutes % minutes)
    return datetime.fromtimestamp(floored * 60, tz=timezone.utc)


def resample_closed(candles: list[FeatureCandle], minutes: int, timeframe: str) -> list[FeatureCandle]:
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    source = [c for c in candles if c.is_closed]
    if not source:
        return []
    groups: dict[datetime, list[FeatureCandle]] = {}
    for candle in source:
        groups.setdefault(floor_time(candle.open_time, minutes), []).append(candle)
    result: list[FeatureCandle] = []
    expected_5m = minutes // 5 if minutes >= 5 else 1
    for start in sorted(groups):
        bucket = sorted(groups[start], key=lambda c: c.open_time)
        if minutes % 5 == 0 and len(bucket) < expected_5m:
            continue
        result.append(
            FeatureCandle(
                symbol=bucket[0].symbol,
                timeframe=timeframe,
                open_time=start,
                open=bucket[0].open,
                high=max(c.high for c in bucket),
                low=min(c.low for c in bucket),
                close=bucket[-1].close,
                volume=sum(c.volume for c in bucket),
                is_closed=True,
            )
        )
    return result
