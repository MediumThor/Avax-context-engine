"""Mandatory leakage probes: future bars cannot change a snapshot at T."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from packages.features import assemble_features
from packages.features.resample import period_end
from tests.features.conftest import make_candle, series, utc


def _perturb_after(candles, as_of):
    out = []
    for candle in candles:
        if period_end(candle.open_time, candle.timeframe) > as_of:
            out.append(
                replace(
                    candle,
                    open=900.0,
                    high=950.0,
                    low=850.0,
                    close=925.0,
                    volume=1_000_000.0,
                )
            )
        else:
            out.append(candle)
    return out


def test_perturb_candles_after_t_leaves_feature_snapshot_unchanged():
    start = utc(2026, 1, 1)
    avax = series(600, start=start, price=8.0, step=0.002)
    btc = series(600, start=start, price=90_000.0, step=5.0, symbol="BTCUSDT")
    eth = series(600, start=start, price=3_000.0, step=0.4, symbol="ETHUSDT")
    as_of = utc(2026, 1, 2, 10, 35)

    before = assemble_features(avax, as_of, btc_5m=btc, eth_5m=eth)
    after = assemble_features(
        _perturb_after(avax, as_of),
        as_of,
        btc_5m=_perturb_after(btc, as_of),
        eth_5m=_perturb_after(eth, as_of),
    )
    assert before.values == after.values
    assert before.to_dict()["availability"] == after.to_dict()["availability"]
    assert before.source_counts == after.source_counts
    assert before.feature_schema_version == after.feature_schema_version


def test_perturb_only_future_btc_and_eth_leaves_relative_features_unchanged():
    start = utc(2026, 1, 1)
    avax = series(400, start=start, price=8.0, step=-0.001)
    btc = series(400, start=start, price=90_000.0, step=3.0, symbol="BTCUSDT")
    eth = series(400, start=start, price=3_200.0, step=-0.2, symbol="ETHUSDT")
    as_of = utc(2026, 1, 2, 3, 15)
    baseline = assemble_features(avax, as_of, btc_5m=btc, eth_5m=eth)
    mutated = assemble_features(
        avax,
        as_of,
        btc_5m=_perturb_after(btc, as_of),
        eth_5m=_perturb_after(eth, as_of),
    )
    rel_keys = [k for k in baseline.values if k.startswith("rel_") or k.startswith("btc_") or k.startswith("eth_")]
    for key in rel_keys:
        assert baseline.values[key] == mutated.values[key], key


def test_appending_future_extreme_bars_does_not_change_t():
    start = utc(2026, 1, 1, 0, 0)
    hist = series(200, start=start, price=10.0, step=0.01)
    as_of = period_end(hist[-1].open_time, "5m")
    extra = [
        make_candle(
            hist[-1].open_time + timedelta(minutes=5 * i),
            50.0 + i,
            open_=49.0,
            volume=9_999,
        )
        for i in range(1, 40)
    ]
    a = assemble_features(hist, as_of)
    b = assemble_features(hist + extra, as_of)
    assert a.values == b.values


def test_multiple_as_of_points_are_stable_under_suffix_noise():
    start = utc(2026, 1, 1)
    candles = series(500, start=start, price=7.5, step=0.003)
    checkpoints = [
        utc(2026, 1, 1, 12, 0),
        utc(2026, 1, 1, 16, 35),
        utc(2026, 1, 2, 0, 0),
        utc(2026, 1, 2, 8, 15),
    ]
    for as_of in checkpoints:
        clean = assemble_features(candles, as_of)
        noisy = assemble_features(_perturb_after(candles, as_of), as_of)
        assert clean.values == noisy.values
        assert clean.availability["avax_5m"].known_at == as_of or (
            clean.availability["avax_5m"].known_at is not None
            and clean.availability["avax_5m"].known_at <= as_of
        )
