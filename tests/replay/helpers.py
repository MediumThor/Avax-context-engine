"""Vendored test helpers for WAVE2-37. Not a production replay implementation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from packages.context_engine import Candle


UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
SYMBOL = "AVAXUSDT"

# ForecastOutcome field names from wiki/Data-Contracts.md plus obvious aliases.
# A forecast row written at T must not carry these keys anywhere in its payload.
FORECAST_OUTCOME_KEYS = frozenset(
    {
        "actual",
        "actuals",
        "matured_at",
        "outcome",
        "outcomes",
        "realized",
        "realized_close_above_origin",
        "realized_cum_log_return",
        "realized_max_adverse_excursion",
        "realized_max_favorable_excursion",
        "scores",
        "y_true",
    }
)

HIGHER_TIMEFRAMES = ("1h", "4h", "1d")


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware UTC")
    dt = dt.astimezone(UTC)
    if dt.microsecond:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def period_end_5m(candle: Candle) -> datetime:
    return candle.open_time.astimezone(UTC) + timedelta(minutes=5)


def make_candle(
    i: int,
    *,
    open_price: float,
    close: float,
    is_closed: bool = True,
    start: datetime = T0,
    high: float | None = None,
    low: float | None = None,
    volume: float | None = None,
) -> Candle:
    open_time = start + timedelta(minutes=5 * i)
    top = max(open_price, close)
    bottom = min(open_price, close)
    return Candle(
        SYMBOL,
        "5m",
        open_time,
        open_price,
        top + 0.01 if high is None else high,
        bottom - 0.01 if low is None else low,
        close,
        100.0 + i if volume is None else volume,
        is_closed=is_closed,
    )


def declining_series(n: int = 384, start_price: float = 12.0, step: float = -0.02) -> list[Candle]:
    out: list[Candle] = []
    price = start_price
    for i in range(n):
        close = price + step
        out.append(make_candle(i, open_price=price, close=close))
        price = close
    return out


def rising_from(prev: Candle, n: int, step: float = 0.08) -> list[Candle]:
    out: list[Candle] = []
    price = prev.close
    start_index = int((prev.open_time - T0).total_seconds() // 60 // 5) + 1
    for i in range(n):
        close = price + step
        out.append(make_candle(start_index + i, open_price=price, close=close))
        price = close
    return out


def mutate_after(candles: list[Candle], t_index: int) -> list[Candle]:
    """Copy the prefix through t_index-1 and replace later bars with wild OHLC."""
    out: list[Candle] = []
    for i, candle in enumerate(candles):
        if i < t_index:
            out.append(candle)
            continue
        out.append(
            Candle(
                candle.symbol,
                candle.timeframe,
                candle.open_time,
                80.0,
                95.0,
                70.0,
                90.0,
                1_000_000.0,
                is_closed=True,
            )
        )
    return out


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return iso_utc(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def outcome_keys_present(payload: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORECAST_OUTCOME_KEYS:
                found.add(key)
            found.update(outcome_keys_present(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(outcome_keys_present(item))
    return found


def forecast_payload_at_t(snapshot, forecasted_at: str) -> dict:
    """ForecastPackage-shaped payload with no ForecastOutcome fields."""
    tf4 = snapshot.timeframes["4h"]
    return {
        "schema_version": "1",
        "symbol": snapshot.symbol,
        "base_timeframe": "5m",
        "forecasted_at": forecasted_at,
        "origin_close": snapshot.timeframes["5m"].close,
        "context_as_of": jsonable(snapshot.as_of),
        "regime_4h": tf4.regime,
        "regime_4h_as_of": jsonable(tf4.as_of),
        "regime_4h_close": tf4.close,
        "regime_4h_evidence": list(tf4.evidence),
        "snapshot": jsonable(snapshot.to_dict()),
        "horizons": [
            {
                "h": horizon,
                "expected_cum_log_return": 0.0,
                "p_close_above_origin": 0.5,
                "q10_cum_log_return": -0.01,
                "q50_cum_log_return": 0.0,
                "q90_cum_log_return": 0.01,
            }
            for horizon in range(1, 11)
        ],
        "calibration_ref": "none-redteam-fixture",
        "health": "valid",
    }


def higher_tf_view(snapshot) -> dict[str, dict]:
    view: dict[str, dict] = {}
    for tf in HIGHER_TIMEFRAMES:
        state = snapshot.timeframes.get(tf)
        if state is None:
            continue
        view[tf] = {
            "regime": state.regime,
            "as_of": state.as_of,
            "close": state.close,
            "evidence": tuple(state.evidence),
            "swing_state": state.swing_state,
            "ema20": state.ema20,
            "ema50": state.ema50,
            "ema200": state.ema200,
        }
    return view


def try_import_replay():
    return pytest.importorskip(
        "packages.context_engine.replay",
        reason=(
            "packages.context_engine.replay is absent on this tree; "
            "required probes use ContextEngine.build_snapshot + ForecastJournal"
        ),
    )
