"""POST /loops/run uses a journaled forecast. It does not emit a new one."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from services.api.runtime import PrototypeRuntime, reset_runtime


def test_loops_run_without_forecast_does_not_emit(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    before = runtime.journal.list_forecasts("AVAXUSDT")
    body = runtime.run_harness_loop("AVAXUSDT")
    after = runtime.journal.list_forecasts("AVAXUSDT")
    assert before == []
    assert after == []
    assert body["accepted"] is True
    assert body["ran"] is False
    assert body["reason"] == "no_journaled_forecast"
    runtime.close()
    reset_runtime()


def test_loops_run_attaches_to_journaled_forecast(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    first = runtime.forecast("AVAXUSDT", persist=True)
    forecast_id = f"AVAXUSDT:{first['forecast']['forecasted_at']}:{first['forecast']['model_id']}"
    sha = runtime.journal.get_forecast(forecast_id)["sha256"]
    count = len(runtime.journal.list_forecasts("AVAXUSDT"))
    again = runtime.run_harness_loop("AVAXUSDT", persist=True)
    assert again["accepted"] is True
    assert again["ran"] is True
    assert again["forecast_id"] == forecast_id
    assert again["persisted"] is True
    assert runtime.journal.get_forecast(forecast_id)["sha256"] == sha
    assert len(runtime.journal.list_forecasts("AVAXUSDT")) == count
    replay = runtime.run_harness_loop(
        "AVAXUSDT",
        as_of=datetime(2026, 9, 2, tzinfo=timezone.utc),
        persist=False,
    )
    assert replay["ran"] is True
    assert replay["persisted"] is False
    runtime.close()

    from services.api.main import app

    reset_runtime()
    client = TestClient(app)
    body = client.post("/api/v1/loops/run").json()
    assert body["accepted"] is True
    assert body["ran"] is True
    assert body["forecast_id"] == forecast_id
    assert "stub" not in (body.get("note") or "").lower()
    reset_runtime()
