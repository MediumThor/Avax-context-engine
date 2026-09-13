# RLH-00 — Persist LoopTraces without rewriting forecasts

```md
Task: Append journaled LoopTraces after a live loop, linked by forecast_id, without mutating the forecast payload or payload_sha256.
Agent: 00
Branch: cursor/persist-loop-traces-8771
Priority: P0
Source main commit: ec91001
Dependency gate: G4 (PR 40 live loop on main)

Why:
Prediction Journal write sequence requires a durable LoopTrace after ForecastPackage commit. Live loops currently exist only in the request wrapper.

Allowed write scope:
- packages/journal/**
- services/api/runtime.py
- services/api/main.py
- tests/test_loop_trace_journal.py
- tests/test_rlh_live_context.py
- wiki/Prediction-Journal.md
- wiki/Recursive-Learning-Contracts.md
- wiki/Build-Roadmap.md
- wiki/Agent-Build-Plan.md
- wiki/tasks/RLH-00-persist-loop-traces.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. Append-only loop_traces table. No UPDATE of payload_json.
2. Persist only after the forecast row exists and the kill switch is off.
3. Replay persist=False does not write a trace.
4. GET /api/v1/loops/{id} returns the stored trace or 404.
5. Forecast payload_sha256 unchanged after the loop is stored.

Acceptance tests:
- first persist writes a trace; second persist is a no-op
- forecast sha256 unchanged
- kill switch writes neither forecast nor trace
- GET returns the stored halt_reason

Finish criteria:
Traces are durable and linked. Forecast rows stay append-only. No confidence claims.
```
