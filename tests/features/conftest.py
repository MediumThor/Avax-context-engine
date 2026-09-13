from __future__ import annotations

from datetime import datetime, timedelta, timezone

from packages.features.types import FeatureCandle


def utc(y: int, m: int, d: int, hh: int = 0, mm: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def make_candle(
    open_time: datetime,
    close: float,
    *,
    symbol: str = "AVAXUSDT",
    timeframe: str = "5m",
    volume: float = 100.0,
    is_closed: bool = True,
    open_: float | None = None,
    high: float | None = None,
    low: float | None = None,
) -> FeatureCandle:
    o = close if open_ is None else open_
    hi = max(o, close) + 0.02 if high is None else high
    lo = min(o, close) - 0.02 if low is None else low
    return FeatureCandle(
        symbol=symbol,
        timeframe=timeframe,
        open_time=open_time,
        open=o,
        high=hi,
        low=lo,
        close=close,
        volume=volume,
        is_closed=is_closed,
    )


def series(
    n: int,
    *,
    start: datetime | None = None,
    price: float = 10.0,
    step: float = 0.01,
    symbol: str = "AVAXUSDT",
    volume: float = 100.0,
) -> list[FeatureCandle]:
    t0 = start or utc(2026, 1, 1)
    out: list[FeatureCandle] = []
    px = price
    for i in range(n):
        nxt = px + step
        out.append(
            make_candle(
                t0 + timedelta(minutes=5 * i),
                nxt,
                symbol=symbol,
                open_=px,
                volume=volume + i,
            )
        )
        px = nxt
    return out
