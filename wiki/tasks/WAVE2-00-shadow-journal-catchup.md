# WAVE2-00 — Shadow-journal closed 5m origins without extra quantiles

```md
Task: On live persist, fill missing closed 5m forecast rows with baseline.drift20. Cap emits per request. Do not emit extra quantile packages. Replay and kill switch do not write.
Agent: 00
Branch: cursor/shadow-journal-catchup-8771
Priority: P0
Source main commit: cebfef8

Why:
The journal only stored T and T-10. Constitution §7 and Prediction-Journal require a row at each eligible 5m close. Extra quantile emits on the request path were rejected as too slow.

Allowed write scope:
- services/api/runtime.py
- tests/test_shadow_journal.py
- wiki/Prediction-Journal.md
- wiki/Agent-Build-Plan.md
- wiki/Build-Roadmap.md
- wiki/tasks/WAVE2-00-shadow-journal-catchup.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. Catch-up walks closed bars whose h=10 close is already known.
2. model_id is baseline.drift20. Existing quantile rows are not rewritten.
3. Budget SHADOW_CATCHUP_BUDGET per live persist.
4. Replay persist=False and kill switch write nothing.
5. No future bar is used.

Finish criteria:
Dense drift20 journal toward every mature-able 5m origin. No promotion claim. No execution.
```
