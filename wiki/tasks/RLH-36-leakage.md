# RLH-36 — Leakage red team

```md
Task: Blocking leakage probes for RLH encoder/loop memory.
Agent: 36
Base: latest main
Integration target: main
Branch: cursor/rlh-36-probes-8771
Model: Composer 2.5 Fast
Priority: P0

Why:
A recursive loop that can see T+1 is worse than a dumb baseline.

Inputs:
- wiki/Recursive-Evaluation.md (Leakage probes)
- services/harness/encoder/builder.py
- services/harness/encoder/tools.py
- services/harness/loop/runner.py

Allowed write scope:
- tests/leakage/rlh/**
- wiki/tasks/RLH-36-leakage.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- production harness fixes except one-line as_of filters in services/harness/encoder/tools.py when probe proves real leak
- deleting or weakening existing probe asserts

Probes (blocking):
1. Future-candle perturbation at T — encoder_memory_hash and LoopTrace content_hash unchanged.
2. Unfinished parent-candle injection — partial/unclosed parent ignored; memory hash unchanged.
3. Tool surface refuses known_at > as_of (analog.search, context.get_hypotheses, forecast.get_history, evaluation.get_metrics).
4. 5m overlay cannot mutate parent timeframe slices; loop final_state preserves 4h regime.
5. Warm-start with outcomes_matured_after refused.
6. Tool call with missing as_of refused (wiki probe #5).

Acceptance tests:
- python3 -m pytest tests/leakage/rlh/test_probes.py -v

Finish criteria:
All probes pass. No production silencing. No weakened asserts.
```
