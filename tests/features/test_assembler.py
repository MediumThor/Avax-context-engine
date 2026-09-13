from datetime import datetime

import pytest

from packages.features import FeatureAssembler, assemble_features
from packages.features.schema import FEATURE_NAMES
from tests.features.conftest import series, utc


def test_assemble_requires_timezone_aware_as_of():
    candles = series(20)
    with pytest.raises(ValueError, match="timezone-aware"):
        assemble_features(candles, datetime(2026, 1, 1, 1, 0))


def test_assemble_requires_a_visible_5m_bar():
    candles = series(5, start=utc(2026, 1, 1, 10, 0))
    with pytest.raises(ValueError, match="no completed AVAX 5m"):
        assemble_features(candles, utc(2026, 1, 1, 10, 0))


def test_default_as_of_is_last_closed_period_end():
    candles = series(30, start=utc(2026, 1, 1, 9, 0))
    snap = assemble_features(candles)
    assert snap.as_of == utc(2026, 1, 1, 11, 30)
    assert snap.known_at == snap.as_of


def test_5m_features_populated_after_warmup():
    candles = series(80, start=utc(2026, 1, 1), price=10.0, step=0.02)
    snap = assemble_features(candles, utc(2026, 1, 1, 6, 40))
    assert snap.values["avax_5m_logret_1"] is not None
    assert snap.values["avax_5m_rsi14"] is not None
    assert snap.values["avax_5m_atr14"] is not None
    assert snap.values["avax_5m_ema20_dist"] is not None
    assert snap.values["avax_5m_vol_ratio_24"] is not None
    assert snap.availability["avax_5m"].closed_bar_count == 80


def test_missing_btc_eth_leaves_relative_none():
    candles = series(40, start=utc(2026, 1, 1))
    snap = assemble_features(candles, utc(2026, 1, 1, 3, 20))
    assert snap.values["rel_avax_btc_logret_1"] is None
    assert snap.values["eth_5m_logret_1"] is None
    assert snap.availability["btc_5m"].closed_bar_count == 0
    assert snap.availability["eth_5m"].known_at is None


def test_class_and_function_api_match():
    candles = series(50)
    as_of = utc(2026, 1, 1, 4, 10)
    a = assemble_features(candles, as_of)
    b = FeatureAssembler().assemble(candles, as_of)
    assert a.to_dict() == b.to_dict()
    assert list(a.values) == list(FEATURE_NAMES)


def test_snapshot_is_deterministic():
    candles = series(120, price=7.8, step=-0.004)
    as_of = utc(2026, 1, 1, 10, 0)
    first = assemble_features(candles, as_of)
    second = assemble_features(list(reversed(candles)), as_of)
    assert first.values == second.values
