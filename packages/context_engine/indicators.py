from __future__ import annotations

from math import sqrt
from typing import Iterable


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


def atr(highs: Iterable[float], lows: Iterable[float], closes: Iterable[float], period: int = 14) -> list[float | None]:
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
