"""Leakage-safe candle visibility and completed-parent resampling.

A bar is visible at ``as_of`` only when it is marked closed AND its period
end is at or before ``as_of``. Incomplete higher-timeframe buckets are dropped.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from . import _lib
from .schema import PRIMARY_TIMEFRAME, TIMEFRAME_MINUTES
from .types import FeatureCandle, as_feature_candle, require_aware

_USING_CONTEXT_ENGINE = False
_resample_closed_impl = _lib.resample_closed

try:
    from packages.context_engine.models import Candle as EngineCandle  # type: ignore
    from packages.context_engine.resample import resample_closed as _ce_resample_closed
except ImportError:
    EngineCandle = None  # type: ignore[misc, assignment]
else:
    _USING_CONTEXT_ENGINE = True

    def _resample_closed_impl(  # type: ignore[no-redef]
        candles: list[FeatureCandle], minutes: int, timeframe: str
    ) -> list[FeatureCandle]:
        engine_bars = [
            EngineCandle(
                symbol=c.symbol,
                timeframe=c.timeframe,
                open_time=c.open_time,
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume,
                is_closed=c.is_closed,
            )
            for c in candles
        ]
        out = _ce_resample_closed(engine_bars, minutes, timeframe)
        return [as_feature_candle(c) for c in out]


def using_context_engine() -> bool:
    return _USING_CONTEXT_ENGINE


def timeframe_minutes(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return TIMEFRAME_MINUTES[timeframe]


def period_end(open_time: datetime, timeframe: str) -> datetime:
    aware = require_aware(open_time, field_name="open_time")
    return aware + timedelta(minutes=timeframe_minutes(timeframe))


def candle_period_end(candle: FeatureCandle) -> datetime:
    return period_end(candle.open_time, candle.timeframe)


def is_visible_at(candle: FeatureCandle, as_of: datetime) -> bool:
    """True only for closed bars whose entire period is known at ``as_of``."""
    cutoff = require_aware(as_of, field_name="as_of")
    if not candle.is_closed:
        return False
    return candle_period_end(candle) <= cutoff


def visible_candles(
    candles: Sequence[object],
    as_of: datetime,
    *,
    timeframe: str | None = None,
) -> list[FeatureCandle]:
    cutoff = require_aware(as_of, field_name="as_of")
    visible: list[FeatureCandle] = []
    for raw in candles:
        candle = as_feature_candle(raw)
        if timeframe is not None and candle.timeframe != timeframe:
            continue
        if is_visible_at(candle, cutoff):
            visible.append(candle)
    visible.sort(key=lambda c: c.open_time)
    return visible


def completed_parents(
    candles_5m: Sequence[object],
    as_of: datetime,
    timeframe: str,
) -> list[FeatureCandle]:
    """Resample visible 5m bars into completed parent candles only."""
    if timeframe == PRIMARY_TIMEFRAME:
        return visible_candles(candles_5m, as_of, timeframe=PRIMARY_TIMEFRAME)
    minutes = timeframe_minutes(timeframe)
    source = visible_candles(candles_5m, as_of)
    resampled = _resample_closed_impl(source, minutes, timeframe)
    cutoff = require_aware(as_of, field_name="as_of")
    return [c for c in resampled if period_end(c.open_time, timeframe) <= cutoff]


def last_known_at(candles: Iterable[FeatureCandle]) -> datetime | None:
    ends = [candle_period_end(c) for c in candles]
    if not ends:
        return None
    last = max(ends)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last
