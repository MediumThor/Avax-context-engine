"""Dedicated drift20 journal drain. No extra quantile emit."""

from fastapi.testclient import TestClient

from packages.harness.kill_switch import engage
from services.api.main import app
from services.api.runtime import (
    SHADOW_CATCHUP_BUDGET,
    SHADOW_CATCHUP_MODEL,
    PrototypeRuntime,
    reset_runtime,
)


def test_drain_writes_more_drift20_than_request_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    reset_runtime()
    runtime = PrototypeRuntime(tmp_path / "m.db", tmp_path / "j.db", use_fixture=True)
    first = runtime.forecast("AVAXUSDT", persist=True)
    assert first["shadow_journal"]["remaining"] > 0
    before = [row for row in runtime.journal.list_forecasts("AVAXUSDT") if row["model_id"] == SHADOW_CATCHUP_MODEL]
    quant_before = [row for row in runtime.journal.list_forecasts("AVAXUSDT") if row["model_id"] != SHADOW_CATCHUP_MODEL]
    sha_by_id = {row["id"]: row["sha256"] for row in runtime.journal.list_forecasts("AVAXUSDT")}
    drained = runtime.drain_shadow_journal("AVAXUSDT", budget=200)
    assert drained["blocked"] is False
    assert drained["wrote"] > 0
    assert drained["wrote"] > SHADOW_CATCHUP_BUDGET or drained["remaining"] == 0
    assert drained["remaining"] < first["shadow_journal"]["remaining"]
    after = runtime.journal.list_forecasts("AVAXUSDT")
    drift = [row for row in after if row["model_id"] == SHADOW_CATCHUP_MODEL]
    quant = [row for row in after if row["model_id"] != SHADOW_CATCHUP_MODEL]
    assert len(drift) == len(before) + drained["wrote"]
    assert len(quant) == len(quant_before)
    for row in after:
        if row["id"] in sha_by_id:
            assert row["sha256"] == sha_by_id[row["id"]]
        if row["model_id"] == SHADOW_CATCHUP_MODEL:
            assert row["payload"]["horizons"][0]["p_close_above_origin"] is None
    runtime.close()
    reset_runtime()


def test_catchup_endpoint_and_kill_switch(tmp_path, monkeypatch):
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    client = TestClient(app)
    live = client.get("/api/v1/forecast/current", params={"symbol": "AVAXUSDT"})
    assert live.status_code == 200
    remaining = live.json()["shadow_journal"]["remaining"]
    drained = client.post("/api/v1/journal/catchup", params={"symbol": "AVAXUSDT", "budget": 80})
    assert drained.status_code == 200
    body = drained.json()
    assert body["model_id"] == SHADOW_CATCHUP_MODEL
    assert body["blocked"] is False
    if remaining > 0:
        assert body["wrote"] > 0
    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(tmp_path / "kill-switch.json"))
    engage(
        "block drain",
        actor="test",
        path=tmp_path / "kill-switch.json",
        tasks_path=tmp_path / "active-tasks.json",
        health_path=tmp_path / "recursive-health.json",
    )
    blocked = client.post("/api/v1/journal/catchup", params={"symbol": "AVAXUSDT"})
    assert blocked.status_code == 423
    reset_runtime()
