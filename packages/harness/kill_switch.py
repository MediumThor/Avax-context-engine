"""Recursive-agent kill switch.

Engaging severs ALL Recursive Learning Harness / wave-1 agent work.
It does not delete journaled traces, rewrite forecasts, or enable execution.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path("artifacts/watcher/kill-switch.json")
HEALTH_PATH = Path("artifacts/watcher/recursive-health.json")
TASKS_PATH = Path("artifacts/watcher/active-tasks.json")


class AgentsSevered(RuntimeError):
    """Raised when a loop or agent task tries to run while the switch is engaged."""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def switch_path() -> Path:
    return Path(os.environ.get("AVAX_KILL_SWITCH_PATH", DEFAULT_PATH))


def empty_state() -> dict[str, Any]:
    return {
        "engaged": False,
        "engaged_at": None,
        "reset_at": None,
        "reason": None,
        "actor": None,
        "severed_task_ids": [],
        "effects": [],
        "events": [],
    }


def load(path: Path | None = None) -> dict[str, Any]:
    target = path or switch_path()
    if not target.exists():
        return empty_state()
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("kill-switch file is not an object")
    return payload


def save(state: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or switch_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def is_engaged(path: Path | None = None) -> bool:
    return bool(load(path).get("engaged"))


def assert_not_severed(path: Path | None = None) -> None:
    state = load(path)
    if state.get("engaged"):
        raise AgentsSevered(
            f"recursive agents severed at {state.get('engaged_at')}: {state.get('reason')}"
        )


def _append_event(state: dict[str, Any], kind: str, actor: str, reason: str) -> None:
    events = list(state.get("events") or [])
    events.append({"at": utcnow(), "kind": kind, "actor": actor, "reason": reason})
    state["events"] = events


def _sever_roster(tasks_path: Path | None = None) -> list[str]:
    roster = tasks_path or TASKS_PATH
    if not roster.exists():
        return []
    data = json.loads(roster.read_text(encoding="utf-8"))
    ids: list[str] = []
    for task in data.get("tasks", []):
        if task.get("status") in {"active", "launched"}:
            task["status"] = "severed"
            task["severed_at"] = utcnow()
            ids.append(str(task.get("id")))
    data["kill_switch"] = "engaged"
    roster.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return ids


def _freeze_health(health_path: Path | None = None) -> None:
    target = health_path or HEALTH_PATH
    if not target.exists():
        payload: dict[str, Any] = {}
    else:
        payload = json.loads(target.read_text(encoding="utf-8"))
    payload["promotion_frozen"] = True
    payload["status"] = "agents-severed"
    notes = list(payload.get("notes") or [])
    notes.append("Kill switch engaged: recursive agents severed.")
    payload["notes"] = notes[-20:]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def engage(
    reason: str,
    actor: str = "operator",
    *,
    path: Path | None = None,
    tasks_path: Path | None = None,
    health_path: Path | None = None,
) -> dict[str, Any]:
    if not reason or not reason.strip():
        raise ValueError("kill switch requires a reason")
    state = load(path)
    severed = _sever_roster(tasks_path)
    _freeze_health(health_path)
    state.update(
        {
            "engaged": True,
            "engaged_at": utcnow(),
            "reset_at": None,
            "reason": reason.strip(),
            "actor": actor,
            "severed_task_ids": severed,
            "effects": [
                "halt_new_loops",
                "freeze_promotion",
                "sever_active_agent_tasks",
                "harness_degraded",
            ],
        }
    )
    _append_event(state, "engage", actor, reason.strip())
    return save(state, path)


def _restore_roster(tasks_path: Path | None = None) -> None:
    roster = tasks_path or TASKS_PATH
    if not roster.exists():
        return
    data = json.loads(roster.read_text(encoding="utf-8"))
    for task in data.get("tasks", []):
        if task.get("status") == "severed":
            task["status"] = "launched"
            task.pop("severed_at", None)
    data["kill_switch"] = "reset"
    roster.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def reset(
    reason: str,
    actor: str = "operator",
    *,
    path: Path | None = None,
    tasks_path: Path | None = None,
    health_path: Path | None = None,
) -> dict[str, Any]:
    if not reason or not reason.strip():
        raise ValueError("reset requires a reason")
    state = load(path)
    _restore_roster(tasks_path)
    state.update(
        {
            "engaged": False,
            "reset_at": utcnow(),
            "reason": None,
            "actor": actor,
            "severed_task_ids": [],
            "effects": [],
        }
    )
    _append_event(state, "reset", actor, reason.strip())
    target = health_path or HEALTH_PATH
    if target.exists():
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["promotion_frozen"] = False
        payload["status"] = "kill-switch-reset"
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return save(state, path)
