"""Append-only maturation of journaled forecasts.

Never mutates a forecast row. Uses only candles whose close is known at as_of.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Sequence

from packages.journal import ForecastJournal


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _log_ret(later: float, now: float) -> float | None:
    if later <= 0 or now <= 0:
        return None
    return math.log(later / now)


def mature_outcomes(
    journal: ForecastJournal,
    candles: Sequence[Any],
    symbol: str,
    *,
    as_of: datetime | None = None,
) -> dict[str, int]:
    """Write missing outcome rows for horizons whose close is already known."""
    closed = [c for c in candles if getattr(c, "is_closed", True)]
    if as_of is not None:
        cutoff = _aware(as_of)
        closed = [c for c in closed if c.close_time() <= cutoff]
    by_close = {int(c.close_time().timestamp()): i for i, c in enumerate(closed)}
    written = 0
    scanned = 0
    for row in journal.list_forecasts(symbol):
        scanned += 1
        payload = row["payload"]
        try:
            origin_at = _parse_iso(payload["forecasted_at"])
            origin_close = float(payload["origin_close"])
        except (KeyError, TypeError, ValueError):
            continue
        index = by_close.get(int(origin_at.timestamp()))
        if index is None:
            continue
        for horizon in range(1, 11):
            later_i = index + horizon
            if later_i >= len(closed):
                continue
            if journal.has_outcome(row["id"], horizon):
                continue
            later = closed[later_i]
            actual = _log_ret(float(later.close), origin_close)
            if actual is None:
                continue
            wrote = journal.get_or_append_outcome(
                row["id"],
                horizon,
                {
                    "forecast_id": row["id"],
                    "schema_version": "1",
                    "h": horizon,
                    "matured_at": later.close_time().isoformat(),
                    "realized_cum_log_return": actual,
                    "realized_close_above_origin": float(later.close) > origin_close,
                    "origin_close": origin_close,
                    "realized_close": float(later.close),
                },
            )
            if wrote:
                written += 1
    return {"forecasts_scanned": scanned, "outcomes_written": written}
