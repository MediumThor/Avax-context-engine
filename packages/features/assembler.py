"""Leakage-safe multi-timeframe feature assembler.

No model training happens here. Outputs are versioned snapshots only.
"""

from __future__ import annotations

from datetime import datetime
from math import sqrt
from typing import Sequence

from .indicators import atr, ema, realized_volatility, rsi
from .relative import relative_feature_map, window_logret
from .resample import completed_parents, last_known_at, period_end, visible_candles
from .schema import (
    AVAILABILITY_KEYS,
    EMA_SPANS,
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    HIGHER_TIMEFRAMES,
    HTF_RETURN_WINDOWS,
    PRIMARY_TIMEFRAME,
    RETURN_WINDOWS,
)
from .types import AvailabilityRecord, FeatureCandle, FeatureSnapshot, as_feature_candle, require_aware

SLOPE_LOOKBACK = 3
VOL_WINDOW = 24
RANGE_WINDOW = 24
RSI_PERIOD = 14
ATR_PERIOD = 14
VOL_EXPANSION_MULT = 1.5


def _last_closed_as_of(candles: Sequence[object]) -> datetime:
    closed = [as_feature_candle(c) for c in candles if as_feature_candle(c).is_closed]
    if not closed:
        raise ValueError("Need at least one closed 5m candle")
    last = max(closed, key=lambda c: c.open_time)
    return period_end(last.open_time, last.timeframe)


def _geometry(candle: FeatureCandle) -> dict[str, float | None]:
    span = candle.high - candle.low
    body = abs(candle.close - candle.open)
    upper = candle.high - max(candle.open, candle.close)
    lower = min(candle.open, candle.close) - candle.low
    if span <= 0:
        return {
            "body_ratio": 0.0,
            "upper_wick_ratio": 0.0,
            "lower_wick_ratio": 0.0,
            "range_pct": 0.0,
            "close_loc": 0.5,
        }
    return {
        "body_ratio": body / span,
        "upper_wick_ratio": upper / span,
        "lower_wick_ratio": lower / span,
        "range_pct": span / candle.close if candle.close else None,
        "close_loc": (candle.close - candle.low) / span,
    }


def _rolling_extrema(candles: Sequence[FeatureCandle], window: int) -> tuple[float | None, float | None]:
    if len(candles) < window:
        return None, None
    recent = candles[-window:]
    high = max(c.high for c in recent)
    low = min(c.low for c in recent)
    close = candles[-1].close
    if close <= 0 or high <= 0 or low <= 0:
        return None, None
    return close / high - 1.0, close / low - 1.0


def _volume_stats(volumes: Sequence[float], window: int) -> tuple[float | None, float | None, float | None]:
    if len(volumes) < window:
        return None, None, None
    sample = list(volumes[-window:])
    last = sample[-1]
    mean = sum(sample) / window
    var = sum((v - mean) ** 2 for v in sample) / window
    std = sqrt(var)
    zscore = None if std == 0 else (last - mean) / std
    ratio = None if mean == 0 else last / mean
    expansion = 1.0 if mean > 0 and last > VOL_EXPANSION_MULT * mean else 0.0
    return zscore, ratio, expansion


def _ema_stack_score(close: float, ema_last: dict[int, float]) -> float | None:
    ordered = [ema_last.get(span) for span in EMA_SPANS]
    if any(v is None for v in ordered):
        return None
    values = [close, *ordered]
    score = 0.0
    for left, right in zip(values, values[1:]):
        if left > right:
            score += 1.0
        elif left < right:
            score -= 1.0
    return score


def _ema_slope(series: Sequence[float], lookback: int = SLOPE_LOOKBACK) -> float | None:
    if len(series) <= lookback:
        return None
    prev = series[-1 - lookback]
    if prev == 0:
        return None
    return (series[-1] - prev) / prev


def timeframe_feature_map(
    candles: Sequence[FeatureCandle],
    prefix: str,
    windows: tuple[int, ...],
) -> dict[str, float | None]:
    values: dict[str, float | None] = {f"{prefix}logret_{w}": None for w in windows}
    for name in (
        "body_ratio",
        "upper_wick_ratio",
        "lower_wick_ratio",
        "range_pct",
        "close_loc",
        "dist_rolling_high_24",
        "dist_rolling_low_24",
        "rsi14",
        "rsi14_centered",
        "atr14",
        "atr14_pct",
        "realized_vol_24",
        "vol_z_24",
        "vol_ratio_24",
        "vol_expansion",
        "ema_stack_score",
    ):
        values[f"{prefix}{name}"] = None
    for span in EMA_SPANS:
        values[f"{prefix}ema{span}_dist"] = None
        values[f"{prefix}ema{span}_slope"] = None
    if not candles:
        return values

    last = candles[-1]
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    volumes = [c.volume for c in candles]

    for window in windows:
        values[f"{prefix}logret_{window}"] = window_logret(closes, window)

    geometry = _geometry(last)
    for key, value in geometry.items():
        values[f"{prefix}{key}"] = value

    dist_high, dist_low = _rolling_extrema(candles, RANGE_WINDOW)
    values[f"{prefix}dist_rolling_high_24"] = dist_high
    values[f"{prefix}dist_rolling_low_24"] = dist_low

    rsi_series = rsi(closes, RSI_PERIOD)
    rsi_last = rsi_series[-1]
    values[f"{prefix}rsi14"] = rsi_last
    values[f"{prefix}rsi14_centered"] = None if rsi_last is None else (rsi_last - 50.0) / 50.0

    atr_series = atr(highs, lows, closes, ATR_PERIOD)
    atr_last = atr_series[-1]
    values[f"{prefix}atr14"] = atr_last
    values[f"{prefix}atr14_pct"] = None if atr_last is None or last.close <= 0 else atr_last / last.close
    values[f"{prefix}realized_vol_24"] = realized_volatility(closes, VOL_WINDOW)

    zscore, ratio, expansion = _volume_stats(volumes, VOL_WINDOW)
    values[f"{prefix}vol_z_24"] = zscore
    values[f"{prefix}vol_ratio_24"] = ratio
    values[f"{prefix}vol_expansion"] = expansion

    ema_last: dict[int, float] = {}
    for span in EMA_SPANS:
        series = ema(closes, span)
        last_ema = series[-1]
        ema_last[span] = last_ema
        values[f"{prefix}ema{span}_dist"] = None if last.close <= 0 else (last.close - last_ema) / last.close
        values[f"{prefix}ema{span}_slope"] = _ema_slope(series)
    values[f"{prefix}ema_stack_score"] = _ema_stack_score(last.close, ema_last)
    return values


def _availability(timeframe: str, candles: Sequence[FeatureCandle]) -> AvailabilityRecord:
    if not candles:
        return AvailabilityRecord(
            timeframe=timeframe,
            last_closed_open_time=None,
            known_at=None,
            closed_bar_count=0,
        )
    last = candles[-1]
    return AvailabilityRecord(
        timeframe=timeframe,
        last_closed_open_time=last.open_time,
        known_at=last_known_at(candles),
        closed_bar_count=len(candles),
    )


class FeatureAssembler:
    """Assemble a versioned feature snapshot knowable at ``as_of``."""

    schema_version = FEATURE_SCHEMA_VERSION

    def assemble(
        self,
        avax_5m: Sequence[object],
        as_of: datetime | None = None,
        *,
        btc_5m: Sequence[object] | None = None,
        eth_5m: Sequence[object] | None = None,
    ) -> FeatureSnapshot:
        if as_of is None:
            as_of = _last_closed_as_of(avax_5m)
        cutoff = require_aware(as_of, field_name="as_of")

        avax = completed_parents(avax_5m, cutoff, PRIMARY_TIMEFRAME)
        if not avax:
            raise ValueError("no completed AVAX 5m candles at as_of")

        parents: dict[str, list[FeatureCandle]] = {
            tf: completed_parents(avax_5m, cutoff, tf) for tf in HIGHER_TIMEFRAMES
        }
        btc = visible_candles(btc_5m or (), cutoff)
        eth = visible_candles(eth_5m or (), cutoff)

        values: dict[str, float | None] = {}
        values.update(timeframe_feature_map(avax, "avax_5m_", RETURN_WINDOWS))
        for tf in HIGHER_TIMEFRAMES:
            values.update(timeframe_feature_map(parents[tf], f"avax_{tf}_", HTF_RETURN_WINDOWS))
        values.update(relative_feature_map(avax, btc, eth))

        ordered = {name: values.get(name) for name in FEATURE_NAMES}
        availability = {
            "avax_5m": _availability(PRIMARY_TIMEFRAME, avax),
            "avax_15m": _availability("15m", parents["15m"]),
            "avax_1h": _availability("1h", parents["1h"]),
            "avax_4h": _availability("4h", parents["4h"]),
            "avax_1d": _availability("1d", parents["1d"]),
            "btc_5m": _availability("5m", btc),
            "eth_5m": _availability("5m", eth),
        }
        missing_keys = [key for key in AVAILABILITY_KEYS if key not in availability]
        if missing_keys:
            raise ValueError(f"missing availability keys: {missing_keys}")

        return FeatureSnapshot(
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            symbol=avax[-1].symbol,
            as_of=cutoff,
            known_at=cutoff,
            values=ordered,
            availability=availability,
            source_counts={
                "avax_5m": len(avax),
                "avax_15m": len(parents["15m"]),
                "avax_1h": len(parents["1h"]),
                "avax_4h": len(parents["4h"]),
                "avax_1d": len(parents["1d"]),
                "btc_5m": len(btc),
                "eth_5m": len(eth),
            },
        )


def assemble_features(
    avax_5m: Sequence[object],
    as_of: datetime | None = None,
    *,
    btc_5m: Sequence[object] | None = None,
    eth_5m: Sequence[object] | None = None,
) -> FeatureSnapshot:
    return FeatureAssembler().assemble(avax_5m, as_of, btc_5m=btc_5m, eth_5m=eth_5m)


def feature_schema_version() -> str:
    return FEATURE_SCHEMA_VERSION
