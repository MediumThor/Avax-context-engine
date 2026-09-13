"""Chart timeframe switcher resamples closed 5m bars without lookahead."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from packages.context_engine.models import Candle
from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from services.api.runtime import PrototypeRuntime, normalize_chart_tf, reset_runtime


def test_normalize_chart_tf_degrades_invalid():
    assert normalize_chart_tf("4h") == "4h"
    assert normalize_chart_tf("3m") == "5m"
    assert normalize_chart_tf(None) == "5m"


def test_market_payload_includes_resampled_chart_candles(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    payload = runtime.market_payload("AVAXUSDT", persist=False, chart_timeframe="4h")
    assert payload["chart_timeframe"] == "4h"
    by_tf = payload["chart_candles"]
    assert set(by_tf) == {"5m", "15m", "1h", "4h", "1d", "1w"}
    assert by_tf["5m"] == payload["candles"]
    assert len(by_tf["4h"]) < len(by_tf["5m"])
    assert len(by_tf["4h"]) >= 8
    assert all(row["time"] % (240 * 60) == 0 for row in by_tf["4h"])
    runtime.close()
    reset_runtime()


def test_htf_chart_ignores_future_5m_after_as_of(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    candles = sept_2026_failed_breakout("AVAXUSDT")
    cut = candles[bounce_start_index(candles) - 1].close_time()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    before = runtime.market_payload("AVAXUSDT", as_of=cut, persist=False)["chart_candles"]["4h"]
    last = candles[-1]
    runtime.store.insert_many(
        "fixture",
        [
            Candle(
                last.symbol,
                last.timeframe,
                last.open_time + timedelta(minutes=5),
                99.0,
                99.0,
                99.0,
                99.0,
                last.volume,
                is_closed=True,
            )
        ],
    )
    after = runtime.market_payload("AVAXUSDT", as_of=cut, persist=False)["chart_candles"]["4h"]
    assert before == after
    assert all(row["close"] != 99.0 for row in after)
    last_open = datetime.fromtimestamp(after[-1]["time"], tz=timezone.utc)
    assert last_open <= cut
    runtime.close()
    reset_runtime()


def test_market_tf_query_echoes_and_invalid_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    client = TestClient(app)
    ok = client.get("/api/v1/market/AVAXUSDT", params={"tf": "1h"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["chart_timeframe"] == "1h"
    assert body["chart_candles"]["1h"]
    bad = client.get("/api/v1/market/AVAXUSDT", params={"tf": "3m"})
    assert bad.status_code == 200
    assert bad.json()["chart_timeframe"] == "5m"
    reset_runtime()
