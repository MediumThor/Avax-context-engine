"""HTF-gated drift is leakage-safe and never a promotion."""

from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from packages.models.htf_regime_drift import (
    MODEL_ID,
    emit_htf_regime_forecast,
    parent_regime,
    walk_forward_htf_regime,
)


def _bar(open_time: datetime, close: float, prev: float | None = None) -> Candle:
    open_px = prev if prev is not None else close
    high = max(open_px, close) + 0.01
    low = min(open_px, close) - 0.01
    return Candle("AVAXUSDT", "5m", open_time, open_px, high, low, close, 10.0, True)


def _declining_then_bounce() -> list[Candle]:
    """Three closed 4h declines, then a 5m bounce so drift20 is positive."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out: list[Candle] = []
    price = 10.0
    # 3 full 4h buckets = 144 five-minute bars, steadily down.
    for i in range(144):
        nxt = price - 0.01
        out.append(_bar(start + timedelta(minutes=5 * i), nxt, price))
        price = nxt
    # 20-bar bounce so trailing drift20 is up while 4h sequence stays down.
    for i in range(20):
        nxt = price + 0.02
        out.append(_bar(start + timedelta(minutes=5 * (144 + i)), nxt, price))
        price = nxt
    return out


def test_bearish_4h_gates_positive_5m_drift():
    candles = _declining_then_bounce()
    assert parent_regime(candles) == "bearish"
    forecast = emit_htf_regime_forecast(candles)
    assert forecast["model_id"] == MODEL_ID
    assert forecast["promotion_allowed"] is False
    assert forecast["parent_regime"] == "bearish"
    h1 = forecast["horizons"][0]
    assert h1["drift20_cum_log_return"] > 0
    assert h1["htf_regime_cum_log_return"] == 0.0
    assert h1["expected_cum_log_return"] == 0.0
    assert forecast["horizons"][9]["htf_regime_cum_log_return"] == 0.0


def test_later_completed_4h_is_ignored_on_the_as_of_prefix():
    base = _declining_then_bounce()
    assert parent_regime(base) == "bearish"
    start = base[-1].open_time + timedelta(minutes=5)
    price = base[-1].close
    future: list[Candle] = []
    for i in range(48):
        nxt = price + 0.5
        future.append(_bar(start + timedelta(minutes=5 * i), nxt, price))
        price = nxt
    prefix = emit_htf_regime_forecast(base)
    assert prefix["parent_regime"] == "bearish"
    assert prefix["horizons"][0]["htf_regime_cum_log_return"] == 0.0
    cut = base[-1].close_time()
    mixed = base + future
    visible = [c for c in mixed if c.close_time() <= cut]
    after = emit_htf_regime_forecast(visible)
    assert after["parent_regime"] == "bearish"
    assert after["horizons"] == prefix["horizons"]
    fixture = sept_2026_failed_breakout("AVAXUSDT")
    stamp = fixture[bounce_start_index(fixture) - 1].close_time()
    visible_fx = [c for c in fixture if c.is_closed and c.close_time() <= stamp]
    a = emit_htf_regime_forecast(visible_fx)
    b = emit_htf_regime_forecast([c for c in fixture if c.close_time() <= stamp])
    assert a["horizons"] == b["horizons"]


def test_walk_forward_never_promotes_on_fixture():
    candles = sept_2026_failed_breakout("AVAXUSDT")
    report = walk_forward_htf_regime(candles, horizons=10, min_history=200, step=40)
    assert report["promotion_allowed"] is False
    assert report["origin_count"] > 0
    h1 = report["horizons"]["1"]
    assert h1["sample_count"] > 0
    assert isinstance(h1["htf_mae_minus_drift20_mae"], float)
    assert h1["htf_regime"]["mae"] >= 0
    # A win on this fixture is evidence, not a gate.
    assert "not a promotion" in report["notes"]
