# WAVE2-00 — Journaled drift20 MAE from matured catch-up rows

```md
Task: Score matured journal rows for drift20 point-forecast MAE/RMSE. Mature drain-written rows on the drain path. Do not invent Brier/ECE from null p.
Agent: 00
Branch: cursor/journal-drift20-mae-8771
Priority: P1
Source main commit: 570b8b7

Why:
Catch-up/drain journals baseline.drift20 with p_close_above_origin null. score_journaled_forecasts therefore never produces Brier from those rows. Realized outcomes still exist. Constitution §6/§13 want that error measured on the journal, not only on the stepped walk-forward slice.

Allowed write scope:
- packages/models/journal_scores.py
- packages/models/probability_walkforward.py (MIN_MAE constant only if needed)
- services/api/runtime.py
- apps/web/src/App.tsx
- tests/test_journal_drift20_mae.py
- wiki/Prediction-Journal.md
- wiki/Simulation-Accuracy.md
- wiki/tasks/WAVE2-00-journal-drift20-mae.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. Use realized_cum_log_return vs drift20_cum_log_return / expected_cum_log_return.
2. Null MAE until MIN_MAE. Null Brier stays null when p is null.
3. Drain calls mature_outcomes. Does not rewrite forecast hashes.
4. promotion_allowed remains false.
5. Accuracy n uses the journal sample when drift20.source is journal.

Finish: Journaled drift20 MAE is evidence-gated. Not a promotion. No execution.
```
