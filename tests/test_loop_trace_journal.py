"""Append-only LoopTraces linked to journaled forecasts."""

from fastapi.testclient import TestClient

from packages.journal import ForecastJournal
from services.api.runtime import PrototypeRuntime, reset_runtime


def test_append_loop_trace_does_not_rewrite_forecast(tmp_path):
    journal = ForecastJournal(tmp_path / "j.db")
    digest, created = journal.get_or_append(
        forecast_id="f-loop",
        symbol="AVAXUSDT",
        forecasted_at="2026-09-02T02:00:00Z",
        model_id="test",
        payload={"horizons": [1]},
    )
    assert created is True
    trace = {
        "id": "loop-test-1",
        "schema_version": "1",
        "symbol": "AVAXUSDT",
        "as_of": "2026-09-02T02:00:00Z",
        "encoder_memory_id": "encmem-1",
        "encoder_memory_hash": "sha256:" + ("a" * 64),
        "context_snapshot_id": "snap-1",
        "forecast_package_id": "f-loop",
        "harness_version": "rlh-0.1.0",
        "tool_schema_version": "1",
        "commit_sha": "test",
        "warm_start_from_trace_id": None,
        "steps": [{"t": 1, "kind": "HALT"}],
        "final_state": {},
        "halt": {"reason": "no_change"},
        "content_hash": "sha256:" + ("b" * 64),
        "journaled_at": "2026-09-02T02:00:00Z",
    }
    loop_id, wrote = journal.get_or_append_loop_trace("f-loop", trace)
    assert wrote is True
    assert loop_id == "loop-test-1"
    again, wrote_again = journal.get_or_append_loop_trace("f-loop", trace)
    assert wrote_again is False
    assert again == "loop-test-1"
    stored = journal.get_forecast("f-loop")
    assert stored["sha256"] == digest
    assert stored["payload"] == {"horizons": [1]}
    listed = journal.list_loop_traces("f-loop")
    assert len(listed) == 1
    assert listed[0]["halt"]["reason"] == "no_change"
    fetched = journal.get_loop_trace("loop-test-1")
    assert fetched["forecast_id"] == "f-loop"
    assert fetched["trace"]["id"] == "loop-test-1"
    journal.close()


def test_live_persist_stores_trace_and_api_can_read_it(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    first = runtime.forecast("AVAXUSDT", persist=True)
    assert first["loop"]["ran"] is True
    assert first["loop"]["persisted"] is True
    forecast_id = f"AVAXUSDT:{first['forecast']['forecasted_at']}:{first['forecast']['model_id']}"
    before = runtime.journal.get_forecast(forecast_id)
    traces = runtime.journal.list_loop_traces(forecast_id)
    assert len(traces) == 1
    second = runtime.forecast("AVAXUSDT", persist=True)
    assert second["loop"]["persisted"] is False
    after = runtime.journal.get_forecast(forecast_id)
    assert after["sha256"] == before["sha256"]
    assert after["payload"]["horizons"] == before["payload"]["horizons"]
    assert len(runtime.journal.list_loop_traces(forecast_id)) == 1
    replay = runtime.forecast("AVAXUSDT", persist=False)
    assert replay["loop"]["ran"] is True
    assert replay["loop"]["persisted"] is False
    runtime.close()

    from services.api.main import app

    reset_runtime()
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    client = TestClient(app)
    body = client.get(f"/api/v1/loops/{traces[0]['id']}").json()
    assert body["forecast_id"] == forecast_id
    assert body["trace"]["halt"]["reason"] == first["loop"]["halt_reason"]
    assert client.get("/api/v1/loops/missing").status_code == 404
    reset_runtime()
