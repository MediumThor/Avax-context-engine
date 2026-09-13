from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from packages.harness.kill_switch import (
    AgentsSevered,
    assert_not_severed,
    engage,
    load,
    reset,
    switch_path,
)

app = FastAPI(title="AVAX Context Engine API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class KillSwitchRequest(BaseModel):
    reason: str = Field(min_length=1)
    actor: str = "operator"


def _paths() -> dict[str, Path]:
    return {
        "path": switch_path(),
        "tasks_path": Path(os.environ.get("AVAX_WATCHER_TASKS_PATH", "artifacts/watcher/active-tasks.json")),
        "health_path": Path(os.environ.get("AVAX_WATCHER_HEALTH_PATH", "artifacts/watcher/recursive-health.json")),
    }


@app.get("/health")
def health() -> dict:
    killed = load()
    return {
        "status": "agents-severed" if killed.get("engaged") else "ok",
        "mode": "read-only",
        "execution": False,
        "kill_switch_engaged": bool(killed.get("engaged")),
    }


@app.get("/api/v1/system")
def system() -> dict:
    killed = load()
    return {
        "project": "AVAX Context Engine",
        "execution_enabled": False,
        "forecast_horizons": 10,
        "base_timeframe": "5m",
        "prototype_branch": "main",
        "kill_switch_engaged": bool(killed.get("engaged")),
        "harness": "degraded" if killed.get("engaged") else "ready",
    }


@app.get("/api/v1/agents/kill-switch")
def get_kill_switch() -> dict:
    return load()


@app.post("/api/v1/agents/kill-switch")
def post_kill_switch(body: KillSwitchRequest) -> dict:
    try:
        return engage(body.reason, actor=body.actor, **_paths())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/agents/kill-switch/reset")
def post_kill_switch_reset(body: KillSwitchRequest) -> dict:
    try:
        return reset(
            body.reason,
            actor=body.actor,
            path=_paths()["path"],
            health_path=_paths()["health_path"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/loops/run")
def run_loop() -> dict:
    try:
        assert_not_severed()
    except AgentsSevered as exc:
        raise HTTPException(status_code=423, detail=str(exc)) from exc
    return {"accepted": True, "harness_version": "rlh-0.1.0", "note": "stub runner for prototype"}
