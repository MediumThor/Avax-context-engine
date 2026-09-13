"""First live pull keeps enough 5m history for 1d/1w resample."""

from datetime import datetime, timedelta, timezone

from packages.context_engine.models import Candle
from services.api.runtime import (
    DEFAULT_LIVE_LOOKBACK_DAYS,
    PrototypeRuntime,
    _chart_by_timeframe,
    chart_source_limit,
    live_lookback_days,
    reset_runtime,
)


def _bar(open_time: datetime, close: float, prev: float | None = None) -> Candle:
    open_px = prev if prev is not None else close
    high = max(open_px, close) + 0.01
    low = min(open_px, close) - 0.01
    return Candle("AVAXUSDT", "5m", open_time, open_px, high, low, close, 10.0, True)


def test_live_lookback_days_clamps(monkeypatch):
    monkeypatch.delenv("AVAX_LIVE_LOOKBACK_DAYS", raising=False)
    assert live_lookback_days() == DEFAULT_LIVE_LOOKBACK_DAYS
    assert chart_source_limit() == DEFAULT_LIVE_LOOKBACK_DAYS * 288
    monkeypatch.setenv("AVAX_LIVE_LOOKBACK_DAYS", "3")
    assert live_lookback_days() == 10
    monkeypatch.setenv("AVAX_LIVE_LOOKBACK_DAYS", "400")
    assert live_lookback_days() == 180
    monkeypatch.setenv("AVAX_LIVE_LOOKBACK_DAYS", "nope")
    assert live_lookback_days() == DEFAULT_LIVE_LOOKBACK_DAYS


def test_first_live_pull_requests_lookback_days(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    monkeypatch.setenv("AVAX_LIVE_LOOKBACK_DAYS", "90")
    seen: dict[str, object] = {}

    class FakeClient:
        def __init__(self, timeout: float = 30.0):
            seen["timeout"] = timeout

        def close(self) -> None:
            return None

        def iter_recent_days(self, symbol, interval, days, end=None):
            seen["symbol"] = symbol
            seen["interval"] = interval
            seen["days"] = days
            return []

        def fetch_klines(self, *args, **kwargs):
            raise AssertionError("first pull must use iter_recent_days, not incremental fetch")

    monkeypatch.setattr("packages.market_data.BinanceVisionClient", FakeClient)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    rows = runtime._pull_closed_live("AVAXUSDT")
    assert rows == []
    assert seen["days"] == 90
    assert seen["interval"] == "5m"
    assert seen["timeout"] == 30.0
    runtime.close()
    reset_runtime()


def test_incremental_live_pull_uses_start(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    seen: dict[str, object] = {}
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)

    class FakeClient:
        def __init__(self, timeout: float = 12.0):
            seen["timeout"] = timeout

        def close(self) -> None:
            return None

        def iter_recent_days(self, *args, **kwargs):
            raise AssertionError("incremental refresh must not re-pull the full lookback")

        def fetch_klines(self, symbol, interval, start_ms, end_ms, limit=1000):
            seen["start_ms"] = start_ms
            seen["interval"] = interval
            return []

    monkeypatch.setattr("packages.market_data.BinanceVisionClient", FakeClient)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    runtime._pull_closed_live("AVAXUSDT", start=start)
    assert seen["start_ms"] == int(start.timestamp() * 1000)
    assert seen["timeout"] == 12.0
    runtime.close()
    reset_runtime()


def test_chart_1d_1w_from_ninety_day_5m():
    start = datetime(2026, 4, 6, tzinfo=timezone.utc)  # Monday
    n = 90 * 288
    price = 20.0
    bars: list[Candle] = []
    for i in range(n):
        nxt = price + 0.01
        bars.append(_bar(start + timedelta(minutes=5 * i), nxt, price))
        price = nxt
    by_tf = _chart_by_timeframe(bars, 1000)
    assert len(by_tf["1d"]) >= 80
    assert len(by_tf["1w"]) >= 10
    assert len(by_tf["1w"]) < len(by_tf["1d"]) < len(by_tf["5m"])
