"""Live Binance path: refresh closed 5m bars, never silently become the fixture."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from packages.context_engine.models import Candle
from services.api.runtime import SOURCE, PrototypeRuntime, reset_runtime


def _align_5m(now: datetime) -> datetime:
    aligned = now.astimezone(timezone.utc).replace(second=0, microsecond=0)
    return aligned - timedelta(minutes=aligned.minute % 5)


def _bar(symbol: str, open_time: datetime, close: float) -> Candle:
    return Candle(symbol, "5m", open_time, close, close + 0.01, close - 0.01, close, 10.0, True)


def _series(symbol: str, n: int, last_open: datetime, last_close: float = 7.31) -> list[Candle]:
    start = last_open - timedelta(minutes=5 * (n - 1))
    out: list[Candle] = []
    for i in range(n):
        price = last_close - (n - 1 - i) * 0.0004
        out.append(_bar(symbol, start + timedelta(minutes=5 * i), round(price, 4)))
    return out


def test_live_failure_does_not_become_fixture(tmp_path, monkeypatch):
    def boom(self, symbol: str, after=None):
        raise OSError("binance down")

    monkeypatch.setattr(PrototypeRuntime, "_pull_live_candles", boom)
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    with pytest.raises(RuntimeError, match="live market data unavailable"):
        runtime.candles("AVAXUSDT")
    assert runtime.use_fixture is False
    assert runtime.store.load(SOURCE, "AVAXUSDT", "5m") == []
    runtime.close()


def test_stale_store_appends_new_closed_candles(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    last_open = _align_5m(now) - timedelta(minutes=5)
    stale_last = last_open - timedelta(hours=2)
    stale = _series("AVAXUSDT", 40, stale_last, last_close=7.28)
    fresh = _series("AVAXUSDT", 3, last_open, last_close=7.31)

    def pull(self, symbol: str, after=None):
        if symbol != "AVAXUSDT":
            return _series(symbol, 40, last_open, last_close=100.0)
        return fresh

    monkeypatch.setattr(PrototypeRuntime, "_pull_live_candles", pull)
    monkeypatch.setattr(PrototypeRuntime, "_pull_last_price", lambda self, symbol: 7.31)
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    runtime.store.insert_many(SOURCE, stale)
    got = runtime.candles("AVAXUSDT", limit=80)
    assert got[-1].close == pytest.approx(7.31)
    assert got[-1].open_time == last_open
    assert any(c.open_time == stale[0].open_time for c in got)
    runtime.close()


def test_fresh_store_skips_network_pull(tmp_path, monkeypatch):
    last_open = _align_5m(datetime.now(timezone.utc)) - timedelta(minutes=5)
    existing = _series("AVAXUSDT", 30, last_open, last_close=7.305)
    calls = {"n": 0}

    def pull(self, symbol: str, after=None):
        calls["n"] += 1
        raise AssertionError("fresh bars must not pull")

    monkeypatch.setattr(PrototypeRuntime, "_pull_live_candles", pull)
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    runtime.store.insert_many(SOURCE, existing)
    got = runtime.candles("AVAXUSDT")
    assert calls["n"] == 0
    assert got[-1].close == pytest.approx(7.305)
    runtime.close()


def test_api_live_market_is_binance_not_fixture(tmp_path, monkeypatch):
    last_open = _align_5m(datetime.now(timezone.utc)) - timedelta(minutes=5)
    avax = _series("AVAXUSDT", 180, last_open, last_close=7.308)
    btc = _series("BTCUSDT", 180, last_open, last_close=115000.0)

    def pull(self, symbol: str, after=None):
        return btc if symbol == "BTCUSDT" else avax

    monkeypatch.setenv("AVAX_USE_FIXTURE", "0")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    monkeypatch.setattr(PrototypeRuntime, "_pull_live_candles", pull)
    monkeypatch.setattr(PrototypeRuntime, "_pull_last_price", lambda self, symbol: 7.31)
    reset_runtime()
    from services.api.main import app

    body = TestClient(app).get("/api/v1/market/AVAXUSDT").json()
    assert body["source"] == SOURCE
    assert body["health"]["status"] != "fixture"
    assert body["price_source"] == "ticker"
    assert body["last_price"] == pytest.approx(7.31)
    assert body["execution_enabled"] is False
    assert body["candles"][-1]["close"] == pytest.approx(7.308)
    reset_runtime()


def test_api_live_failure_is_503_not_fixture(tmp_path, monkeypatch):
    def boom(self, symbol: str, after=None):
        raise OSError("binance down")

    monkeypatch.setenv("AVAX_USE_FIXTURE", "0")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    monkeypatch.setattr(PrototypeRuntime, "_pull_live_candles", boom)
    reset_runtime()
    from services.api.main import app

    res = TestClient(app).get("/api/v1/market/AVAXUSDT")
    assert res.status_code == 503
    assert "live market data unavailable" in res.text
    reset_runtime()
