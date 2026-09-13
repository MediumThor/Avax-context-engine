from datetime import datetime, timedelta, timezone

import pytest

from packages.context_engine import Candle, ContextEngine
from packages.context_engine.replay import (
    ENGINE_VERSION,
    SCHEMA_VERSION,
    ContextReplay,
    knowable_candles,
    period_end,
    replay,
    replay_bytes,
    snapshot_as_of,
)


UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


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
        "AVAXUSDT",
        "5m",
        open_time,
        open_price,
        top + 0.01 if high is None else high,
        bottom - 0.01 if low is None else low,
        close,
        100.0 + i if volume is None else volume,
        is_closed=is_closed,
    )


def declining_series(n: int = 384, start_price: float = 10.0, step: float = -0.01) -> list[Candle]:
    out: list[Candle] = []
    price = start_price
    for i in range(n):
        close = price + step
        out.append(make_candle(i, open_price=price, close=close))
        price = close
    return out


def rising_from(prev: Candle, n: int, step: float = 0.04) -> list[Candle]:
    out: list[Candle] = []
    price = prev.close
    start_index = int((prev.open_time - T0).total_seconds() // 60 // 5) + 1
    for i in range(n):
        close = price + step
        out.append(make_candle(start_index + i, open_price=price, close=close))
        price = close
    return out


def test_deterministic_replay_same_candles_same_snapshots():
    candles = declining_series(120)
    shuffled = list(reversed(candles))
    store = ContextReplay()
    first = store.replay(candles)
    second = store.replay(list(candles))
    third = store.replay(shuffled)
    assert first.snapshots == second.snapshots == third.snapshots
    assert first.transitions == second.transitions == third.transitions
    assert [s.payload_sha256 for s in first.snapshots] == [s.payload_sha256 for s in second.snapshots]
    assert replay_bytes(candles) == replay_bytes(shuffled)
    assert replay_bytes(candles) == replay_bytes(candles)


def test_unfinished_candle_does_not_mutate_as_of_snapshot():
    candles = declining_series(80)
    as_of = period_end(candles[39])
    store = ContextReplay()
    baseline = store.snapshot_as_of(candles, as_of)
    unfinished = make_candle(
        40,
        open_price=candles[39].close,
        close=candles[39].close + 1.5,
        is_closed=False,
    )
    # Unfinished bar whose clock interval already ended, plus one still open.
    late_unfinished = Candle(
        "AVAXUSDT",
        "5m",
        candles[39].open_time,
        1.0,
        9.0,
        0.5,
        8.5,
        99999.0,
        is_closed=False,
    )
    mutated = candles + [unfinished, late_unfinished]
    after = store.snapshot_as_of(mutated, as_of)
    assert after == baseline
    assert after.to_bytes() == baseline.to_bytes()
    assert unfinished not in knowable_candles(mutated, as_of)
    assert late_unfinished not in knowable_candles(mutated, as_of)


def test_perturb_candles_after_t_leaves_snapshot_at_t_unchanged():
    candles = declining_series(160)
    as_of = period_end(candles[79])
    store = ContextReplay()
    original = store.snapshot_as_of(candles, as_of)
    perturbed = []
    for i, candle in enumerate(candles):
        if i <= 79:
            perturbed.append(candle)
            continue
        perturbed.append(
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
    after = store.snapshot_as_of(perturbed, as_of)
    assert after == original
    assert after.payload_sha256 == original.payload_sha256
    assert after.to_bytes() == original.to_bytes()
    future_closes = {c.close for c in perturbed[80:]}
    payload = after.to_dict()
    for tf_state in payload["timeframes"].values():
        assert tf_state["close"] not in future_closes


def test_point_in_time_query_returns_only_information_knowable_at_t():
    candles = declining_series(200)
    as_of = period_end(candles[99])
    store = ContextReplay()
    snap = store.snapshot_as_of(candles, as_of)
    visible = knowable_candles(candles, as_of)
    assert visible == candles[:100]
    assert snap.known_at <= as_of
    assert snap.as_of <= as_of
    payload = snap.to_dict()
    visible_closes = {c.close for c in visible}
    future = candles[100:]
    future_closes = {c.close for c in future}
    future_times = {c.open_time for c in future}
    for tf_name, tf_state in payload["timeframes"].items():
        tf_as_of = datetime.fromisoformat(tf_state["as_of"].replace("Z", "+00:00"))
        assert tf_as_of <= as_of
        assert tf_state["close"] in visible_closes
        assert tf_state["close"] not in future_closes
        assert tf_as_of not in future_times
        if tf_name != "5m":
            # Parent bars exist only after a complete bucket of 5m children.
            minutes = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}[tf_name]
            assert (as_of - T0).total_seconds() >= minutes * 60
    replayed = store.replay(candles).as_of(as_of)
    assert replayed == snap


def test_5m_relief_does_not_overwrite_completed_4h_bearish_parent():
    # 8 complete 4H parents of persistent decline (48 * 5m per 4H).
    decline = declining_series(48 * 8, start_price=12.0, step=-0.02)
    store = ContextReplay()
    before = store.snapshot_as_of(decline, period_end(decline[-1]))
    assert "4h" in before.timeframes
    assert before.timeframes["4h"]["regime"] == "bearish"
    parent_as_of = before.timeframes["4h"]["as_of"]
    parent_close = before.timeframes["4h"]["close"]

    relief = rising_from(decline[-1], n=12, step=0.08)
    after = store.snapshot_as_of(decline + relief, period_end(relief[-1]))
    assert after.timeframes["4h"]["regime"] == "bearish"
    assert after.timeframes["4h"]["as_of"] == parent_as_of
    assert after.timeframes["4h"]["close"] == parent_close
    assert after.timeframes["4h"]["regime"] != "bullish"
    # Incomplete new 4H parent (12 of 48 five-minute bars) must not appear.
    parent_time = datetime.fromisoformat(parent_as_of.replace("Z", "+00:00"))
    assert after.timeframes["4h"]["as_of"] == before.timeframes["4h"]["as_of"]
    assert period_end(relief[-1]) - parent_time < timedelta(hours=4)


def test_engine_and_schema_version_recorded_on_persisted_snapshots():
    candles = declining_series(48)
    store = ContextReplay()
    snap = store.snapshot_as_of(candles, period_end(candles[-1]))
    payload = snap.to_dict()
    assert snap.engine_version == ENGINE_VERSION
    assert snap.schema_version == SCHEMA_VERSION
    assert payload["engine_version"] == ENGINE_VERSION
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["engine_version"]
    assert payload["schema_version"]
    series = store.replay(candles)
    assert series.engine_version == ENGINE_VERSION
    assert series.schema_version == SCHEMA_VERSION
    assert all(item.engine_version == ENGINE_VERSION for item in series.snapshots)
    assert all(item.schema_version == SCHEMA_VERSION for item in series.snapshots)
    assert ContextEngine().build_snapshot(candles).schema_version == snap.schema_version


def test_naive_as_of_is_rejected():
    candles = declining_series(10)
    with pytest.raises(ValueError, match="timezone-aware"):
        snapshot_as_of(candles, datetime(2026, 1, 1, 1, 0))


def test_module_helpers_match_class():
    candles = declining_series(36)
    as_of = period_end(candles[-1])
    assert snapshot_as_of(candles, as_of) == ContextReplay().snapshot_as_of(candles, as_of)
    assert replay(candles).snapshots == ContextReplay().replay(candles).snapshots
