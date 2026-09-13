"""Unfinished parent candles must not leak into higher-timeframe features."""

from __future__ import annotations

from dataclasses import replace

from packages.features import assemble_features
from packages.features.resample import completed_parents
from tests.features.conftest import series, utc


def _prefix_through(candles, last_open):
    return [c for c in candles if c.open_time <= last_open]


def test_unfinished_15m_parent_does_not_leak_at_1035():
    # 10:30-10:45 15m bar is open at 10:35.
    start = utc(2026, 1, 1, 8, 0)
    candles = series(40, start=start, price=10.0, step=0.01)
    as_of = utc(2026, 1, 1, 10, 35)
    snap = assemble_features(candles, as_of)
    parents = completed_parents(candles, as_of, "15m")
    assert parents
    assert parents[-1].open_time == utc(2026, 1, 1, 10, 15)
    assert snap.availability["avax_15m"].last_closed_open_time == utc(2026, 1, 1, 10, 15)
    assert snap.availability["avax_15m"].known_at == utc(2026, 1, 1, 10, 30)

    # Extreme unfinished 10:30 5m (part of open 15m) already in series; replace it.
    poisoned = [
        replace(c, close=c.close + 50.0, high=c.high + 50.0) if c.open_time == utc(2026, 1, 1, 10, 30) else c
        for c in candles
    ]
    # 10:30 5m is closed at 10:35, so 5m features MAY change. 15m must not.
    poisoned_snap = assemble_features(poisoned, as_of)
    fifteen = [k for k in snap.values if k.startswith("avax_15m_")]
    for key in fifteen:
        assert snap.values[key] == poisoned_snap.values[key], key


def test_unfinished_1h_parent_matches_series_cut_before_hour():
    start = utc(2026, 1, 1, 6, 0)
    full = series(80, start=start, price=9.0, step=-0.005)
    as_of = utc(2026, 1, 1, 10, 35)
    # Last completed 1h at 10:35 is 09:00-10:00, last 5m of that hour opens 09:55.
    cut = _prefix_through(full, utc(2026, 1, 1, 9, 55))
    from_full = assemble_features(full, as_of)
    from_cut = assemble_features(cut, as_of)
    hour_keys = [k for k in from_full.values if k.startswith("avax_1h_")]
    for key in hour_keys:
        assert from_full.values[key] == from_cut.values[key], key
    assert from_full.availability["avax_1h"].last_closed_open_time == utc(2026, 1, 1, 9, 0)
    assert from_full.availability["avax_1h"].known_at == utc(2026, 1, 1, 10, 0)
    assert completed_parents(full, as_of, "1h")[-1].open_time == utc(2026, 1, 1, 9, 0)


def test_poisoning_open_1h_bucket_does_not_change_1h_features():
    start = utc(2026, 1, 1, 6, 0)
    candles = series(80, start=start, price=9.0, step=0.004)
    as_of = utc(2026, 1, 1, 10, 35)
    baseline = assemble_features(candles, as_of)
    poisoned = []
    for c in candles:
        if utc(2026, 1, 1, 10, 0) <= c.open_time <= utc(2026, 1, 1, 10, 30):
            poisoned.append(replace(c, open=1.0, high=80.0, low=0.5, close=70.0, volume=9e6))
        else:
            poisoned.append(c)
    mutated = assemble_features(poisoned, as_of)
    for key in [k for k in baseline.values if k.startswith("avax_1h_")]:
        assert baseline.values[key] == mutated.values[key], key
    # 5m snapshot can change because 10:30 5m is closed at 10:35.
    assert mutated.values["avax_5m_logret_1"] != baseline.values["avax_5m_logret_1"]


def test_1h_features_update_only_after_parent_closes():
    start = utc(2026, 1, 1, 8, 0)
    candles = series(48, start=start, price=10.0, step=0.02)
    at_1035 = assemble_features(candles, utc(2026, 1, 1, 10, 35))
    at_1100 = assemble_features(candles, utc(2026, 1, 1, 11, 0))
    assert at_1035.availability["avax_1h"].last_closed_open_time == utc(2026, 1, 1, 9, 0)
    assert at_1100.availability["avax_1h"].last_closed_open_time == utc(2026, 1, 1, 10, 0)
    assert at_1035.values["avax_1h_logret_1"] != at_1100.values["avax_1h_logret_1"]


def test_unfinished_4h_and_1d_parents_do_not_leak():
    start = utc(2026, 1, 1, 0, 0)
    candles = series(200, start=start, price=8.2, step=-0.001)
    as_of = utc(2026, 1, 1, 10, 35)
    snap = assemble_features(candles, as_of)
    # Last completed 4h before 10:35 is 08:00-12:00 still open; so 04:00-08:00.
    assert snap.availability["avax_4h"].last_closed_open_time == utc(2026, 1, 1, 4, 0)
    assert snap.availability["avax_4h"].known_at == utc(2026, 1, 1, 8, 0)
    # 1d 2026-01-01 is still open at 10:35; no completed daily parent yet.
    assert snap.availability["avax_1d"].last_closed_open_time is None
    assert snap.availability["avax_1d"].known_at is None
    assert snap.values["avax_1d_logret_1"] is None

    poisoned = [
        replace(c, close=c.close * 3, high=c.high * 3, volume=c.volume * 50)
        if c.open_time >= utc(2026, 1, 1, 8, 0)
        else c
        for c in candles
    ]
    mutated = assemble_features(poisoned, as_of)
    for key in [k for k in snap.values if k.startswith("avax_4h_") or k.startswith("avax_1d_")]:
        assert snap.values[key] == mutated.values[key], key


def test_daily_parent_appears_at_utc_midnight():
    start = utc(2026, 1, 1, 0, 0)
    candles = series(300, start=start, price=8.0, step=0.002)
    before = assemble_features(candles, utc(2026, 1, 1, 23, 55))
    after = assemble_features(candles, utc(2026, 1, 2, 0, 0))
    assert before.availability["avax_1d"].closed_bar_count == 0
    assert after.availability["avax_1d"].closed_bar_count == 1
    assert after.availability["avax_1d"].last_closed_open_time == utc(2026, 1, 1, 0, 0)
    assert after.availability["avax_1d"].known_at == utc(2026, 1, 2, 0, 0)
