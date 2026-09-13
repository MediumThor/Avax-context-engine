"""Shadow-journal missing 5m origins with drift20. No extra quantile emit."""

from datetime import datetime, timezone

from packages.harness.kill_switch import engage
from services.api.runtime import (
    SHADOW_CATCHUP_BUDGET,
    SHADOW_CATCHUP_MODEL,
    PrototypeRuntime,
    reset_runtime,
)


def test_live_persist_catchup_writes_drift20_not_extra_quantiles(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    first = runtime.forecast("AVAXUSDT", persist=True)
    rows = runtime.journal.list_forecasts("AVAXUSDT")
    drift = [row for row in rows if row["model_id"] == SHADOW_CATCHUP_MODEL]
    quant = [row for row in rows if row["model_id"] != SHADOW_CATCHUP_MODEL]
    assert first["shadow_journal"]["wrote"] == len(drift)
    assert first["shadow_journal"]["wrote"] <= SHADOW_CATCHUP_BUDGET
    assert first["shadow_journal"]["remaining"] >= 0
    assert len(quant) <= 2
    last_close = runtime.candles("AVAXUSDT")[-1].close_time()
    for row in drift:
        stamp = datetime.fromisoformat(str(row["forecasted_at"]).replace("Z", "+00:00"))
        assert stamp <= last_close
        assert row["payload"]["model_id"] == SHADOW_CATCHUP_MODEL
        p = row["payload"]["horizons"][0]["p_close_above_origin"]
        assert p is None or 0.0 <= p <= 1.0
    sha_by_id = {row["id"]: row["sha256"] for row in rows}
    second = runtime.forecast("AVAXUSDT", persist=True)
    again = runtime.journal.list_forecasts("AVAXUSDT")
    for row in again:
        if row["id"] in sha_by_id:
            assert row["sha256"] == sha_by_id[row["id"]]
    assert second["shadow_journal"]["wrote"] >= 0
    if first["shadow_journal"]["remaining"] > 0:
        assert second["shadow_journal"]["wrote"] > 0
    runtime.close()


def test_replay_and_kill_switch_do_not_shadow_journal(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    as_of = datetime(2026, 9, 2, tzinfo=timezone.utc)
    replay = runtime.forecast("AVAXUSDT", as_of=as_of, persist=False)
    assert replay["shadow_journal"]["wrote"] == 0
    assert runtime.journal.list_forecasts("AVAXUSDT") == []
    runtime.close()

    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(tmp_path / "kill-switch.json"))
    engage(
        "block shadow journal",
        actor="test",
        path=tmp_path / "kill-switch.json",
        tasks_path=tmp_path / "active-tasks.json",
        health_path=tmp_path / "recursive-health.json",
    )
    reset_runtime()
    blocked = PrototypeRuntime(tmp_path / "m2.db", tmp_path / "j2.db", use_fixture=True)
    out = blocked.forecast("AVAXUSDT", persist=True)
    assert out["kill_switch_blocked_write"] is True
    assert blocked.journal.list_forecasts("AVAXUSDT") == []
    blocked.close()
    reset_runtime()
