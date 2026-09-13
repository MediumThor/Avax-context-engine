"""Chart timeframe switcher: display bars change; regime stack does not."""

from __future__ import annotations

from fastapi.testclient import TestClient

from packages.fixtures import bounce_start_index, sept_2026_failed_breakout
from services.api.runtime import reset_runtime


def _fixture_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    from services.api.main import app

    return TestClient(app)


def test_invalid_timeframe_is_400(tmp_path, monkeypatch):
    client = _fixture_client(tmp_path, monkeypatch)
    res = client.get("/api/v1/market/AVAXUSDT", params={"timeframe": "3m"})
    assert res.status_code == 400
    reset_runtime()


def test_4h_chart_does_not_change_4h_regime(tmp_path, monkeypatch):
    client = _fixture_client(tmp_path, monkeypatch)
    five = client.get("/api/v1/market/AVAXUSDT", params={"timeframe": "5m"}).json()
    four = client.get("/api/v1/market/AVAXUSDT", params={"timeframe": "4h"}).json()
    assert five["chart_timeframe"] == "5m"
    assert four["chart_timeframe"] == "4h"
    assert five["snapshot"]["timeframes"]["4h"]["regime"] == four["snapshot"]["timeframes"]["4h"]["regime"]
    assert five["snapshot"]["timeframes"]["4h"]["as_of"] == four["snapshot"]["timeframes"]["4h"]["as_of"]
    assert four["forecast"]["forecast"]["horizons"][0]["h"] == 1
    times = [row["time"] for row in four["candles"]]
    assert times == sorted(times)
    assert len(times) >= 2
    assert times[1] - times[0] == 4 * 3600
    reset_runtime()


def test_candles_endpoint_returns_closed_15m(tmp_path, monkeypatch):
    client = _fixture_client(tmp_path, monkeypatch)
    body = client.get("/api/v1/market/AVAXUSDT/candles", params={"timeframe": "15m"}).json()
    assert body["timeframe"] == "15m"
    assert body["execution_enabled"] is False
    times = [row["time"] for row in body["candles"]]
    assert len(times) >= 3
    assert times[1] - times[0] == 15 * 60
    reset_runtime()


def test_replay_as_of_hides_later_htf_bars(tmp_path, monkeypatch):
    client = _fixture_client(tmp_path, monkeypatch)
    candles = sept_2026_failed_breakout()
    idx = bounce_start_index(candles)
    as_of = candles[idx - 1].close_time().isoformat()
    live = client.get("/api/v1/market/AVAXUSDT/candles", params={"timeframe": "1h"}).json()
    replay = client.get(
        "/api/v1/market/AVAXUSDT/candles",
        params={"timeframe": "1h", "as_of": as_of},
    ).json()
    assert replay["replay"] is True
    assert replay["candles"][-1]["time"] < live["candles"][-1]["time"]
    reset_runtime()
