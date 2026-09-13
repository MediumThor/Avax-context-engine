"""Leakage-safe analog retrieval.

Matches are prior origins whose h=10 outcome is already known at T.
Distance uses only the prefix visible at each origin. Realized h=10
returns are attached only because those closes are <= T. Not a forecast
and not a calibrated confidence score.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Sequence


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return value.astimezone(timezone.utc)


def _fingerprint(closes: Sequence[float]) -> tuple[float, float, float]:
    n = len(closes)

    def logret(bars: int) -> float:
        if n <= bars or closes[-1] <= 0 or closes[-1 - bars] <= 0:
            return 0.0
        return math.log(closes[-1] / closes[-1 - bars])

    rets: list[float] = []
    start = max(1, n - 24)
    for i in range(start, n):
        prev, cur = closes[i - 1], closes[i]
        if prev > 0 and cur > 0:
            rets.append(math.log(cur / prev))
    vol = math.sqrt(sum(x * x for x in rets) / len(rets)) if rets else 0.0
    return (logret(12), logret(24), vol)


def retrieve_analogs(
    candles: Sequence[Any],
    as_of: datetime,
    *,
    k: int = 5,
    step: int = 8,
    min_history: int = 80,
) -> tuple[dict[str, Any], ...]:
    cutoff = _aware(as_of)
    closed = [c for c in candles if getattr(c, "is_closed", True) and c.close_time() <= cutoff]
    if len(closed) < min_history + 11:
        return ()
    query = _fingerprint([float(c.close) for c in closed])
    last = len(closed) - 1
    max_origin = last - 10
    scored: list[tuple[float, int, float]] = []
    for index in range(min_history, max_origin + 1, step):
        prefix = [float(c.close) for c in closed[: index + 1]]
        fp = _fingerprint(prefix)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(fp, query)))
        origin_close = float(closed[index].close)
        later_close = float(closed[index + 10].close)
        if origin_close <= 0 or later_close <= 0:
            continue
        realized = math.log(later_close / origin_close)
        scored.append((dist, index, realized))
    scored.sort(key=lambda row: (row[0], row[1]))
    out: list[dict[str, Any]] = []
    for dist, index, realized in scored[:k]:
        out.append(
            {
                "origin_close_time": closed[index].close_time().isoformat(),
                "distance": dist,
                "realized_h10_log_return": realized,
                "known_at": closed[index + 10].close_time().isoformat(),
                "note": "Analog outcome known at T. Not a forecast and not confidence.",
            }
        )
    return tuple(out)
