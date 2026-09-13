# RLH-00 — Replace `/loops/run` stub with a journaled-forecast loop

```md
Task: POST /api/v1/loops/run runs one bounded loop against the latest journaled forecast. It does not emit a new forecast.
Agent: 00
Branch: cursor/loops-run-live-8771
Priority: P1
Source main commit: cfa834c
Dependency gate: LoopTraces + live encoder path on main

Why:
The live forecast path already journals a LoopTrace. `/loops/run` still returned a stub body, so an operator/harness retry could not attach a loop to an existing ForecastPackage without rewriting or re-emitting.

Allowed write scope:
- services/api/runtime.py
- services/api/main.py
- tests/test_loops_run.py
- tests/test_kill_switch.py
- wiki/Recursive-Learning-Contracts.md
- wiki/Recursive-Learning-Harness.md
- wiki/Prediction-Journal.md
- wiki/Agent-Build-Plan.md
- wiki/Build-Roadmap.md
- wiki/tasks/RLH-00-loops-run-live.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. Kill switch still returns 423.
2. No journaled forecast: 200 with ran=false. Do not emit quantiles.
3. Journaled forecast: rebuild snapshot at forecasted_at, run bounded loop, persist trace when as_of is omitted.
4. Replay as_of does not insert a trace.
5. Forecast payload_sha256 is unchanged.

Finish criteria:
Stub replaced. No new forecast emit. No confidence. No execution.
```
