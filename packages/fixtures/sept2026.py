"""Deterministic September 2026 failed-breakout fixture.

Not a claim about exact prints. It encodes the process: fail near ~8.15-8.20,
lose ~8.00, then a 5m relief bounce that must not flip 4H.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle


def _bar(symbol: str, start: datetime, i: int, price: float, high: float | None = None, low: float | None = None) -> Candle:
    close = price
    open_ = price * (1.0002 if i % 2 == 0 else 0.9998)
    hi = high if high is not None else max(open_, close) + 0.012
    lo = low if low is not None else min(open_, close) - 0.012
    return Candle(symbol, "5m", start + timedelta(minutes=5 * i), open_, hi, lo, close, 1000 + i)


def sept_2026_failed_breakout(symbol: str = "AVAXUSDT") -> list[Candle]:
    start = datetime(2026, 8, 20, tzinfo=timezone.utc)
    candles: list[Candle] = []
    i = 0
    price = 7.20
    # Grind toward ~8.05 (about 8 days of 5m).
    for _ in range(8 * 288):
        price = min(8.06, price + 0.00038)
        candles.append(_bar(symbol, start, i, price))
        i += 1
    # Fail at 8.15-8.20: wicks through, closes back below.
    for n in range(2 * 288):
        wick = 8.12 + (n % 7) * 0.012
        price = 8.02 - n * 0.00015
        candles.append(_bar(symbol, start, i, price, high=min(8.22, wick), low=price - 0.03))
        i += 1
    # Lose ~8.00 and trend down to ~7.30.
    for n in range(3 * 288):
        price = 7.95 - n * 0.00075
        candles.append(_bar(symbol, start, i, max(7.28, price)))
        i += 1
    # 5m relief bounce (~20 bars) that must not rewrite 4H.
    bounce_from = candles[-1].close
    for n in range(24):
        price = bounce_from + n * 0.012
        candles.append(_bar(symbol, start, i, price))
        i += 1
    return candles


def bounce_start_index(candles: list[Candle]) -> int:
    return len(candles) - 24


def btc_companion(avax: list[Candle]) -> list[Candle]:
    out = []
    price = 58000.0
    for i, src in enumerate(avax):
        price = price * (0.9997 if src.close < (avax[i - 1].close if i else src.close) else 1.0001)
        out.append(
            Candle(
                "BTCUSDT",
                "5m",
                src.open_time,
                price,
                price * 1.0008,
                price * 0.9992,
                price,
                10.0 + i,
            )
        )
    return out
