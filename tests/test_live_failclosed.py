"""Live Binance ingest must not silently become the September fixture."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from packages.context_engine.models import Candle
from services.api.runtime import (
    SOURCE,
    LiveDataUnavailable,
    PrototypeRuntime,
    reset_runtime,
)


def _bar(symbol: str, open_time: datetime, price: float) -> Candle:
    return Candle(
        symbol,
        "5m",
        open_time,
        price,
        price + 0.1,
        price - 0.1,
        price,
        10.0,
        True,
    )


def test_failed_first_live_pull_does_not_seed_fixture(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)

    def boom(symbol: str, *, start=None):
        raise LiveDataUnavailable("network down")

    monkeypatch.setattr(runtime, "_pull_closed_live", boom)
    with pytest.raises(LiveDataUnavailable):
        runtime.candles("AVAXUSDT")
    assert runtime.use_fixture is False
    assert runtime.store.load("fixture", "AVAXUSDT", "5m") == []
    assert runtime.store.load(SOURCE, "AVAXUSDT", "5m") == []
    runtime.close()
    reset_runtime()


def test_live_refresh_appends_newer_closed_bars(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    t0 = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
    first = _bar("AVAXUSDT", t0, 7.3)
    second = _bar("AVAXUSDT", t0 + timedelta(minutes=5), 7.31)
    runtime.store.insert_many(SOURCE, [first])

    def pull(symbol: str, *, start=None):
        assert symbol == "AVAXUSDT"
        assert start == t0
        return [first, second]

    monkeypatch.setattr(runtime, "_pull_closed_live", pull)
    got = runtime.candles("AVAXUSDT", limit=10)
    assert [c.close for c in got] == [7.3, 7.31]
    assert runtime.use_fixture is False
    runtime.close()
    reset_runtime()


def test_refresh_failure_keeps_prior_live_bars(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=False)
    t0 = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
    prior = _bar("AVAXUSDT", t0, 7.3)
    runtime.store.insert_many(SOURCE, [prior])

    def boom(symbol: str, *, start=None):
        raise LiveDataUnavailable("timeout")

    monkeypatch.setattr(runtime, "_pull_closed_live", boom)
    got = runtime.candles("AVAXUSDT", limit=10)
    assert len(got) == 1
    assert got[0].close == 7.3
    assert runtime.use_fixture is False
    assert runtime.store.load("fixture", "AVAXUSDT", "5m") == []
    runtime.close()
    reset_runtime()


def test_market_503_when_live_empty_and_pull_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("AVAX_USE_FIXTURE", raising=False)
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()

    def boom(self, symbol: str, *, start=None):
        raise LiveDataUnavailable("network down")

    monkeypatch.setattr(PrototypeRuntime, "_pull_closed_live", boom)
    from services.api.main import app

    client = TestClient(app)
    res = client.get("/api/v1/market/AVAXUSDT")
    assert res.status_code == 503
    health = client.get("/health").json()
    data = health.get("data") or {}
    assert data.get("status") != "fixture"
    assert data.get("last_close") is None
    reset_runtime()
