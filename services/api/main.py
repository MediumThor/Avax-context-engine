from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
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
from services.api.runtime import get_runtime

app = FastAPI(title="AVAX Context Engine API", version="0.2.0")
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


def _parse_as_of(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="as_of must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@app.get("/health")
def health() -> dict:
    killed = load()
    payload: dict = {
        "status": "agents-severed" if killed.get("engaged") else "ok",
        "mode": "read-only",
        "execution": False,
        "kill_switch_engaged": bool(killed.get("engaged")),
    }
    try:
        brief = get_runtime().health_brief("AVAXUSDT")
        payload["data"] = brief
        payload["source"] = brief.get("source")
        payload["as_of"] = brief.get("last_close")
    except Exception as exc:
        payload["data"] = {"status": "unknown", "error": str(exc)}
    return payload


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


@app.get("/api/v1/market/{symbol}")
def market(symbol: str, as_of: str | None = Query(default=None), limit: int = Query(default=576, ge=50, le=1000)) -> dict:
    try:
        return get_runtime().market_payload(symbol.upper(), as_of=_parse_as_of(as_of), chart_limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/v1/forecast/current")
def forecast_current(symbol: str = "AVAXUSDT", as_of: str | None = None) -> dict:
    return get_runtime().forecast(symbol.upper(), as_of=_parse_as_of(as_of), persist=_parse_as_of(as_of) is None)


@app.get("/api/v1/forecast/metrics")
def forecast_metrics(symbol: str = "AVAXUSDT", as_of: str | None = None) -> dict:
    return get_runtime().metrics(symbol.upper(), as_of=_parse_as_of(as_of))


@app.get("/api/v1/replay/{symbol}")
def replay(symbol: str, as_of: str = Query(...)) -> dict:
    parsed = _parse_as_of(as_of)
    if parsed is None:
        raise HTTPException(status_code=400, detail="as_of required")
    payload = get_runtime().market_payload(symbol.upper(), as_of=parsed)
    payload["replay"] = True
    return payload


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
        return reset(body.reason, actor=body.actor, **_paths())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/loops/run")
def run_loop() -> dict:
    try:
        assert_not_severed()
    except AgentsSevered as exc:
        raise HTTPException(status_code=423, detail=str(exc)) from exc
    return {"accepted": True, "harness_version": "rlh-0.1.0", "note": "stub runner for prototype"}
