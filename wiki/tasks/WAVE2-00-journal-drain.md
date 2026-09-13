# WAVE2-00 — Drain remaining shadow-journal 5m origins

```md
Task: Add POST /api/v1/journal/catchup that writes more missing mature-able 5m origins as baseline.drift20 only.
Agent: 00
Branch: cursor/journal-drain-8771
Priority: P0

Why:
Request-path catch-up is capped at 24 so market_payload stays fast. Constitution §7 still wants a row at each eligible close.

Allowed write scope:
- services/api/runtime.py
- services/api/main.py
- tests/test_shadow_journal_drain.py
- wiki/Prediction-Journal.md
- wiki/tasks/WAVE2-00-journal-drain.md

Forbidden: CONSTITUTION.md, recursive schemas, baselines.py

Finish: Drain reduces remaining. No extra quantile. Kill switch 423. No execution.
```
