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
