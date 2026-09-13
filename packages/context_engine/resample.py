from __future__ import annotations

from datetime import datetime, timezone

from .models import Candle


def _floor_time(dt: datetime, minutes: int) -> datetime:
    dt = dt.astimezone(timezone.utc)
    epoch_minutes = int(dt.timestamp() // 60)
    floored = epoch_minutes - (epoch_minutes % minutes)
    return datetime.fromtimestamp(floored * 60, tz=timezone.utc)


def resample_closed(candles: list[Candle], minutes: int, timeframe: str) -> list[Candle]:
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    source = [c for c in candles if c.is_closed]
    if not source:
        return []
    groups: dict[datetime, list[Candle]] = {}
    for candle in source:
        groups.setdefault(_floor_time(candle.open_time, minutes), []).append(candle)
    result: list[Candle] = []
    expected_5m = minutes // 5 if minutes >= 5 else 1
    for start in sorted(groups):
        bucket = sorted(groups[start], key=lambda c: c.open_time)
        if minutes % 5 == 0 and len(bucket) < expected_5m:
            continue
        result.append(Candle(symbol=bucket[0].symbol,timeframe=timeframe,open_time=start,open=bucket[0].open,high=max(c.high for c in bucket),low=min(c.low for c in bucket),close=bucket[-1].close,volume=sum(c.volume for c in bucket),is_closed=True))
    return result
