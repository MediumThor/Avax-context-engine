"""Versioned, ordered feature schema for the AVAX 5m assembler.

Breaking changes require a new ``FEATURE_SCHEMA_VERSION``. Names are stable
within a version so journals can join snapshots to later outcomes.
"""

from __future__ import annotations

FEATURE_SCHEMA_VERSION = "avax.features.mtf.v1"

RETURN_WINDOWS: tuple[int, ...] = (1, 2, 3, 6, 12, 24, 48)
HTF_RETURN_WINDOWS: tuple[int, ...] = (1, 2, 3, 6, 12)
EMA_SPANS: tuple[int, ...] = (9, 20, 50, 100, 200)
REL_RETURN_WINDOWS: tuple[int, ...] = (1, 3, 12, 24)
CROSS_RETURN_WINDOWS: tuple[int, ...] = (1, 12, 24)

PRIMARY_TIMEFRAME = "5m"
HIGHER_TIMEFRAMES: tuple[str, ...] = ("15m", "1h", "4h", "1d")
TIMEFRAME_MINUTES: dict[str, int] = {
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


def _geometry_and_vol_names(prefix: str) -> list[str]:
    names = [
        f"{prefix}body_ratio",
        f"{prefix}upper_wick_ratio",
        f"{prefix}lower_wick_ratio",
        f"{prefix}range_pct",
        f"{prefix}close_loc",
        f"{prefix}dist_rolling_high_24",
        f"{prefix}dist_rolling_low_24",
        f"{prefix}rsi14",
        f"{prefix}rsi14_centered",
        f"{prefix}atr14",
        f"{prefix}atr14_pct",
        f"{prefix}realized_vol_24",
        f"{prefix}vol_z_24",
        f"{prefix}vol_ratio_24",
        f"{prefix}vol_expansion",
        f"{prefix}ema_stack_score",
    ]
    for span in EMA_SPANS:
        names.append(f"{prefix}ema{span}_dist")
        names.append(f"{prefix}ema{span}_slope")
    return names


def _return_names(prefix: str, windows: tuple[int, ...]) -> list[str]:
    return [f"{prefix}logret_{window}" for window in windows]


def _timeframe_feature_names(prefix: str, windows: tuple[int, ...]) -> list[str]:
    return _return_names(prefix, windows) + _geometry_and_vol_names(prefix)


def build_feature_names() -> tuple[str, ...]:
    names: list[str] = []
    names.extend(_timeframe_feature_names("avax_5m_", RETURN_WINDOWS))
    for tf in HIGHER_TIMEFRAMES:
        names.extend(_timeframe_feature_names(f"avax_{tf}_", HTF_RETURN_WINDOWS))
    for window in CROSS_RETURN_WINDOWS:
        names.append(f"btc_5m_logret_{window}")
        names.append(f"eth_5m_logret_{window}")
    names.extend(
        [
            "btc_5m_realized_vol_24",
            "eth_5m_realized_vol_24",
        ]
    )
    for window in REL_RETURN_WINDOWS:
        names.append(f"rel_avax_btc_logret_{window}")
        names.append(f"rel_avax_eth_logret_{window}")
    names.extend(
        [
            "rel_avax_btc_corr_24",
            "rel_avax_eth_corr_24",
            "rel_avax_btc_beta_24",
            "rel_avax_eth_beta_24",
            "rel_sync_btc_1",
            "rel_sync_eth_1",
        ]
    )
    return tuple(names)


FEATURE_NAMES: tuple[str, ...] = build_feature_names()

AVAILABILITY_KEYS: tuple[str, ...] = (
    "avax_5m",
    "avax_15m",
    "avax_1h",
    "avax_4h",
    "avax_1d",
    "btc_5m",
    "eth_5m",
)
