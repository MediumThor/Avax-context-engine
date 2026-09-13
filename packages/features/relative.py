"""BTC/ETH relative features from leakage-filtered 5m series."""

from __future__ import annotations

from math import log, sqrt
from typing import Sequence

from .indicators import realized_volatility
from .schema import CROSS_RETURN_WINDOWS, REL_RETURN_WINDOWS
from .types import FeatureCandle

SYNC_ABS_LOGRET = 0.001


def _index_by_open(candles: Sequence[FeatureCandle]) -> dict:
    return {c.open_time: c for c in candles}


def _logret(close_now: float, close_prev: float) -> float | None:
    if close_now <= 0 or close_prev <= 0:
        return None
    return log(close_now / close_prev)


def aligned_closes(
    left: Sequence[FeatureCandle],
    right: Sequence[FeatureCandle],
) -> tuple[list[float], list[float]]:
    right_map = _index_by_open(right)
    a: list[float] = []
    b: list[float] = []
    for candle in left:
        other = right_map.get(candle.open_time)
        if other is None:
            continue
        a.append(candle.close)
        b.append(other.close)
    return a, b


def log_returns(closes: Sequence[float]) -> list[float | None]:
    out: list[float | None] = [None]
    for i in range(1, len(closes)):
        out.append(_logret(closes[i], closes[i - 1]))
    return out


def window_logret(closes: Sequence[float], window: int) -> float | None:
    if len(closes) <= window:
        return None
    return _logret(closes[-1], closes[-1 - window])


def _finite_pair_returns(a: Sequence[float], b: Sequence[float], window: int) -> tuple[list[float], list[float]] | None:
    if len(a) < window + 1 or len(b) < window + 1:
        return None
    ra: list[float] = []
    rb: list[float] = []
    start = len(a) - window
    for i in range(start, len(a)):
        left = _logret(a[i], a[i - 1])
        right = _logret(b[i], b[i - 1])
        if left is None or right is None:
            return None
        ra.append(left)
        rb.append(right)
    return ra, rb


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    return cov / sqrt(var_x * var_y)


def beta(dependent: Sequence[float], factor: Sequence[float]) -> float | None:
    n = len(dependent)
    if n < 3 or n != len(factor):
        return None
    mean_y = sum(dependent) / n
    mean_x = sum(factor) / n
    var_x = sum((x - mean_x) ** 2 for x in factor)
    if var_x == 0:
        return None
    cov = sum((dependent[i] - mean_y) * (factor[i] - mean_x) for i in range(n))
    return cov / var_x


def _sync_flag(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    if abs(a) < SYNC_ABS_LOGRET or abs(b) < SYNC_ABS_LOGRET:
        return 0.0
    return 1.0 if (a > 0) == (b > 0) else 0.0


def relative_feature_map(
    avax: Sequence[FeatureCandle],
    btc: Sequence[FeatureCandle] | None,
    eth: Sequence[FeatureCandle] | None,
) -> dict[str, float | None]:
    values: dict[str, float | None] = {}
    avax_closes = [c.close for c in avax]
    btc_closes = [c.close for c in btc] if btc else []
    eth_closes = [c.close for c in eth] if eth else []

    for window in CROSS_RETURN_WINDOWS:
        values[f"btc_5m_logret_{window}"] = window_logret(btc_closes, window) if btc_closes else None
        values[f"eth_5m_logret_{window}"] = window_logret(eth_closes, window) if eth_closes else None
    values["btc_5m_realized_vol_24"] = realized_volatility(btc_closes, 24) if btc_closes else None
    values["eth_5m_realized_vol_24"] = realized_volatility(eth_closes, 24) if eth_closes else None

    aligned_btc = aligned_closes(avax, btc) if btc else ([], [])
    aligned_eth = aligned_closes(avax, eth) if eth else ([], [])

    for window in REL_RETURN_WINDOWS:
        avax_r = window_logret(aligned_btc[0], window) if aligned_btc[0] else None
        btc_r = window_logret(aligned_btc[1], window) if aligned_btc[1] else None
        values[f"rel_avax_btc_logret_{window}"] = (
            None if avax_r is None or btc_r is None else avax_r - btc_r
        )
        avax_e = window_logret(aligned_eth[0], window) if aligned_eth[0] else None
        eth_r = window_logret(aligned_eth[1], window) if aligned_eth[1] else None
        values[f"rel_avax_eth_logret_{window}"] = (
            None if avax_e is None or eth_r is None else avax_e - eth_r
        )

    pair_btc = _finite_pair_returns(aligned_btc[0], aligned_btc[1], 24) if aligned_btc[0] else None
    pair_eth = _finite_pair_returns(aligned_eth[0], aligned_eth[1], 24) if aligned_eth[0] else None
    values["rel_avax_btc_corr_24"] = pearson(*pair_btc) if pair_btc else None
    values["rel_avax_eth_corr_24"] = pearson(*pair_eth) if pair_eth else None
    values["rel_avax_btc_beta_24"] = beta(pair_btc[0], pair_btc[1]) if pair_btc else None
    values["rel_avax_eth_beta_24"] = beta(pair_eth[0], pair_eth[1]) if pair_eth else None

    avax_1 = window_logret(avax_closes, 1) if avax_closes else None
    btc_1 = window_logret(btc_closes, 1) if btc_closes else None
    eth_1 = window_logret(eth_closes, 1) if eth_closes else None
    values["rel_sync_btc_1"] = _sync_flag(avax_1, btc_1)
    values["rel_sync_eth_1"] = _sync_flag(avax_1, eth_1)
    return values
