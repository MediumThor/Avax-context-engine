# WAVE2-06 — Walk-forward quantile challenger vs drift20

```md
Task: Chronologically score freqai.quantiles.research.v1 q50/coverage against honest drift20 and zero. No promotion.
Agent: 00/06
Branch: cursor/quantile-walkforward-8771
Priority: P0
Source main commit: d725c60d640c235542f4e16117db8472a0effe3a
Dependency gate: G5 Evaluation

Why:
PR 30 journaled next-10 empirical quantiles. Constitution §6 forbids treating that as an improvement until walk-forward vs baselines exists. This increment scores; it does not promote.

Inputs:
- packages/models/freqai_quantiles.py
- packages/models/baselines.py (read-only)
- packages/evaluator/metrics.py
- wiki/Simulation-Accuracy.md

Allowed write scope:
- packages/models/quantile_walkforward.py
- packages/models/__init__.py
- tests/test_quantile_walkforward.py
- wiki/tasks/WAVE2-06-quantile-walkforward.md
- wiki/Build-Roadmap.md
- wiki/Simulation-Accuracy.md
- artifacts/watcher/active-tasks.json

Forbidden write scope:
- CONSTITUTION.md
- packages/models/baselines.py
- packages/contracts/recursive/**
- fabricated ECE / confidence / silent promotion

Implementation requirements:
1. Expanding chronological windows only. No shuffle.
2. At origin t, train/predict using only candles with close_time <= t.
3. Score q50 MAE/RMSE vs drift20 and zero on matured h=1..10 log returns.
4. Report empirical q10–q90 coverage (not ECE unless a calibration module is used).
5. promotion_allowed is always false in this increment. beats_drift20 is null unless every scored horizon has q50 MAE < drift20 MAE; even then do not flip a product promotion flag.

Acceptance tests:
- command: python3 -m pytest -q tests/test_quantile_walkforward.py
  expected: pass
- future perturbation at t does not change the origin-t predictions
- sample_count > 0

Finish criteria:
Walk-forward report exists, leakage test green, no promotion language in API/UI.
```
