import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from packages.harness.kill_switch import AgentsSevered, assert_not_severed, engage, is_engaged, reset
from services.api.main import app


def _paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "path": tmp_path / "kill-switch.json",
        "tasks_path": tmp_path / "active-tasks.json",
        "health_path": tmp_path / "recursive-health.json",
    }


def test_engage_severs_roster_and_blocks_loops(tmp_path: Path):
    paths = _paths(tmp_path)
    paths["tasks_path"].write_text(
        '{"tasks":[{"id":"RLH-27","status":"launched"},{"id":"RLH-30","status":"active"}]}',
        encoding="utf-8",
    )
    state = engage("operator abort", actor="ui", **paths)
    assert state["engaged"] is True
    assert is_engaged(paths["path"]) is True
    assert set(state["severed_task_ids"]) == {"RLH-27", "RLH-30"}
    assert "halt_new_loops" in state["effects"]
    assert "pause_new_forecasts" in state["effects"]
    with pytest.raises(AgentsSevered):
        assert_not_severed(paths["path"])
    health = paths["health_path"].read_text(encoding="utf-8")
    assert "agents-severed" in health


def test_reset_is_logged_and_does_not_delete_events(tmp_path: Path):
    paths = _paths(tmp_path)
    paths["tasks_path"].write_text(
        '{"tasks":[{"id":"RLH-27","status":"launched"}]}',
        encoding="utf-8",
    )
    engage("stop", actor="ui", **paths)
    state = reset("resume prototype", actor="ui", **paths)
    assert state["engaged"] is False
    kinds = [event["kind"] for event in state["events"]]
    assert kinds == ["engage", "reset"]
    assert_not_severed(paths["path"])
    roster = json.loads(paths["tasks_path"].read_text(encoding="utf-8"))
    assert all(task["status"] != "severed" for task in roster["tasks"])


def test_api_kill_switch_blocks_loop_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(tmp_path / "kill-switch.json"))
    monkeypatch.setenv("AVAX_WATCHER_TASKS_PATH", str(tmp_path / "active-tasks.json"))
    monkeypatch.setenv("AVAX_WATCHER_HEALTH_PATH", str(tmp_path / "recursive-health.json"))
    client = TestClient(app)
    assert client.get("/api/v1/agents/kill-switch").json()["engaged"] is False
    assert client.post("/api/v1/loops/run").status_code == 200
    engaged = client.post("/api/v1/agents/kill-switch", json={"reason": "sever all agents", "actor": "ui"})
    assert engaged.status_code == 200
    assert engaged.json()["engaged"] is True
    blocked = client.post("/api/v1/loops/run")
    assert blocked.status_code == 423
    reset_res = client.post(
        "/api/v1/agents/kill-switch/reset",
        json={"reason": "continue prototype", "actor": "ui"},
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["engaged"] is False
    assert client.post("/api/v1/loops/run").status_code == 200


def test_header_pause_button_copy_exists():
    source = Path("apps/web/src/components/AgentKillSwitch.tsx").read_text(encoding="utf-8")
    app = Path("apps/web/src/App.tsx").read_text(encoding="utf-8")
    assert "Pause predictions" in source
    assert "Resume predictions" in source
    assert "<AgentKillSwitch" in app
    assert 'className="topbar"' in app
    assert 'className="topbarMeta"' in app


def test_pause_blocks_new_forecast_journal_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from services.api.runtime import PrototypeRuntime, reset_runtime

    monkeypatch.setenv("AVAX_KILL_SWITCH_PATH", str(tmp_path / "kill-switch.json"))
    monkeypatch.setenv("AVAX_WATCHER_TASKS_PATH", str(tmp_path / "active-tasks.json"))
    monkeypatch.setenv("AVAX_WATCHER_HEALTH_PATH", str(tmp_path / "recursive-health.json"))
    monkeypatch.setenv("AVAX_USE_FIXTURE", "1")
    monkeypatch.setenv("AVAX_MARKET_DB", str(tmp_path / "m.db"))
    monkeypatch.setenv("AVAX_JOURNAL_DB", str(tmp_path / "j.db"))
    reset_runtime()
    client = TestClient(app)
    paused = client.post(
        "/api/v1/agents/kill-switch",
        json={"reason": "pause predictions", "actor": "ui"},
    )
    assert paused.status_code == 200
    assert paused.json()["engaged"] is True
    assert "pause_new_forecasts" in paused.json()["effects"]
    runtime = PrototypeRuntime(tmp_path / "direct-m.db", tmp_path / "direct-j.db", use_fixture=True)
    blocked = runtime.forecast("AVAXUSDT", persist=True)
    assert blocked["kill_switch_blocked_write"] is True
    assert blocked["journaled"] is False
    assert runtime.journal.latest("AVAXUSDT") is None
    runtime.close()
    market = client.get("/api/v1/market/AVAXUSDT").json()
    assert market["forecast"]["kill_switch_blocked_write"] is True
    reset_runtime()
