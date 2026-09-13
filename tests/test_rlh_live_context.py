"""Live EncoderMemory + bounded loop after a journaled forecast."""

from packages.harness.kill_switch import engage
from services.api.runtime import PrototypeRuntime, reset_runtime


def _runtime(tmp_path) -> PrototypeRuntime:
    return PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)


def test_live_forecast_runs_loop_after_journal_without_rewriting_payload(tmp_path):
    runtime = _runtime(tmp_path)
    out = runtime.forecast("AVAXUSDT", persist=True)
    payload = out["forecast"]
    assert out["journaled"] is True
    loop = out["loop"]
    assert loop["ran"] is True
    assert loop["analog_count"] >= 1
    assert loop["hypothesis_ids"]
    assert loop["halt_reason"]
    assert "confidence" not in loop
    assert "Not a forecast" in loop["note"]
    stored = runtime.journal.latest("AVAXUSDT")
    assert stored is not None
    assert stored["payload"]["horizons"] == payload["horizons"]
    assert stored["payload"]["model_id"] == payload["model_id"]
    assert "loop" not in stored["payload"]
    assert out["loop"]["persisted"] is True
    traces = runtime.journal.list_loop_traces(stored["id"])
    assert len(traces) == 1
    assert traces[0]["id"] == out["loop"]["loop_id"]
    runtime.close()


def test_kill_switch_skips_live_loop(tmp_path, monkeypatch):
    switch = tmp_path / "kill-switch.json"
    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(switch))
    engage("test skip loop", actor="test", path=switch)
    runtime = _runtime(tmp_path)
    out = runtime.forecast("AVAXUSDT", persist=True)
    assert out["kill_switch_blocked_write"] is True
    assert out["loop"]["ran"] is False
    assert out["loop"]["reason"] == "kill_switch"
    assert runtime.journal.latest("AVAXUSDT") is None
    runtime.close()
    reset_runtime()
