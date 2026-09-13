from datetime import datetime

from packages.context_engine import ContextEngine
from packages.fixtures import sept_2026_failed_breakout


def test_swing_pivots_are_confirmed_on_fixture():
    candles = sept_2026_failed_breakout()
    snap = ContextEngine().build_snapshot(candles)
    pivots = snap.timeframes["5m"].swing_pivots
    assert pivots
    kinds = {row["kind"] for row in pivots}
    assert kinds <= {"high", "low"}
    assert kinds == {"high", "low"}
    last_open = int(candles[-1].open_time.timestamp())
    for row in pivots:
        assert row["time"] <= last_open
        known = datetime.fromisoformat(row["known_at"])
        assert known <= candles[-1].open_time
        assert row["timeframe"] == "5m"
        assert row["price"] > 0


def test_replay_as_of_cannot_see_later_confirmed_pivots():
    candles = sept_2026_failed_breakout()
    engine = ContextEngine()
    early_as_of = candles[3000].close_time()
    early = engine.build_snapshot(candles, as_of=early_as_of)
    later = engine.build_snapshot(candles)
    early_keys = {(row["time"], row["kind"]) for row in early.timeframes["5m"].swing_pivots}
    later_keys = {(row["time"], row["kind"]) for row in later.timeframes["5m"].swing_pivots}
    assert early_keys
    assert later_keys - early_keys
    for row in early.timeframes["5m"].swing_pivots:
        known = datetime.fromisoformat(row["known_at"])
        assert known <= early.timeframes["5m"].as_of
    four_h = later.timeframes["4h"].swing_pivots
    assert all(row["timeframe"] == "4h" for row in four_h)
