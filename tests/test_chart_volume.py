"""Market payload includes volume and leakage-safe EMA overlays."""

from packages.context_engine.indicators import ema
from packages.context_engine.models import Candle
from packages.fixtures import sept_2026_failed_breakout
from services.api.runtime import PrototypeRuntime, _chart_rows, reset_runtime


def test_market_candles_include_positive_volume(tmp_path):
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    payload = runtime.market_payload("AVAXUSDT", persist=False)
    candles = payload["candles"]
    assert candles
    assert all("volume" in row for row in candles)
    assert all(row["volume"] > 0 for row in candles)
    assert candles[0]["volume"] != candles[-1]["volume"]
    assert all("ema20" in row and "ema50" in row for row in candles)
    runtime.close()
    reset_runtime()


def test_chart_ema_ignores_future_closes():
    series = sept_2026_failed_breakout()[:400]
    before = _chart_rows(series, 80)
    last = series[-1]
    mutated = list(series[:-1]) + [
        Candle(
            last.symbol,
            last.timeframe,
            last.open_time,
            last.open,
            max(last.high, 99.0),
            last.low,
            99.0,
            last.volume,
        )
    ]
    after = _chart_rows(mutated, 80)
    assert [row["ema20"] for row in before[:-1]] == [row["ema20"] for row in after[:-1]]
    assert [row["ema50"] for row in before[:-1]] == [row["ema50"] for row in after[:-1]]
    expected = ema([c.close for c in series], 20)
    assert before[-1]["ema20"] == expected[-1]
