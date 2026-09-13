# WAVE2-07 — Held-out ECE on live/non-fixture data

```md
Task: Report Expected Calibration Error only on a later chronological slice of live/non-fixture forecasts. Fixture and insufficient samples stay null. No promotion.
Agent: 07
Branch: cursor/heldout-live-ece-5716
Priority: P0
Source main commit: 762e7b27044da3451bb18120d733e72a552f6196
Dependency gate: G5 Evaluation
Watcher owner: Agent 00
Review mode: strict-quant

Why:
Watcher next-step item 4. Current ECE is computed on the same walk-forward / journaled pool that includes the September fixture. Constitution §4 and the continuous-improvement chronology rule forbid treating discovery/fixture outcomes as unseen calibration proof. Live Binance Vision rows must be scored on a later held-out window. Fixture mode must never look calibrated.

Inputs:
- wiki/Simulation-Accuracy.md
- wiki/Continuous-Improvement-Directive.md
- wiki/tasks/WATCHER-next-plan.md
- packages/evaluator/calibration.py
- packages/models/journal_scores.py
- packages/models/probability_walkforward.py
- services/api/runtime.py

Allowed write scope:
- packages/evaluator/held_out.py
- packages/evaluator/__init__.py
- packages/models/journal_scores.py
- packages/models/probability_walkforward.py
- packages/models/__init__.py
- services/api/runtime.py
- tests/test_held_out_ece.py
- tests/test_journal_scores.py
- tests/test_probability_walkforward.py
- apps/web/src/components/AccuracyPanel.tsx (ECE definition copy only)
- wiki/tasks/WAVE2-07-heldout-ece.md
- wiki/Simulation-Accuracy.md
- wiki/Prediction-Journal.md
- wiki/Agent-Build-Plan.md
- wiki/Build-Roadmap.md
- wiki/Agent-Roster.md
- wiki/tasks/WATCHER-next-plan.md
- .cursor/plans/heldout-ece.task.md

Forbidden write scope:
- CONSTITUTION.md
- packages/models/baselines.py
- packages/contracts/recursive/**
- services/harness/**
- apps/web/src/App.tsx
- apps/web/src/api/market.ts
- apps/web/src/api/types.ts
- apps/web/src/components/ShadowJournalCard.tsx
- fabricated ECE / confidence / silent promotion
- FreqAI challenger promotion

Assumptions:
- Kill switch is disengaged.
- PR 55 owns the journal-remaining UI; this increment does not touch those files.
- `binance-vision` is the only live candle source on main.
- Existing untagged journal rows inherit the caller/runtime source. Explicit `fixture` tags are never scored as live ECE.
- Held-out fraction is the later 40% by forecast issue time. ECE stays null unless that slice has n >= 15.

Implementation requirements:
1. Stamp `candle_source` on newly journaled forecast payloads (`fixture` or `binance-vision`). Do not rewrite existing rows.
2. Compute reported ECE only on the later chronological slice of live-eligible (p, y) pairs.
3. Fixture runtime, fixture-tagged rows, unknown source, and short held-out windows leave `ece` null with an explicit reason. Do not invent a number.
4. Brier/coverage gates stay on the full matured walk-forward/journal pool unless already gated.
5. `promotion_allowed` remains false. Do not claim FreqAI beats drift20.
6. Future-candle perturbation after `as_of` must not change held-out ECE.

Acceptance tests:
- command: python3 -m pytest -q tests/test_held_out_ece.py tests/test_journal_scores.py tests/test_probability_walkforward.py
  expected: pass
- fixture source with n >= 15 → ece is null
- live source with held-out n >= 15 → ece is a finite number in [0, 1]
- discovery-window miscalibration must not determine the reported ECE
- promotion_allowed is false

Metrics gate:
- baseline: fixture walk-forward may currently emit ECE when n >= 15
- required result: fixture ECE is null; live held-out ECE is defined only when the later slice meets MIN_ECE

Historical regressions:
- September 2026 fixture remains a context/replay case, not a live calibration claim.

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: chronological held-out ECE, not a promotion plan
- known failed approaches: research q50 still loses to drift20 on the fixture; do not promote

Docs to update:
- wiki/Simulation-Accuracy.md
- wiki/Prediction-Journal.md
- wiki/Agent-Build-Plan.md
- wiki/Build-Roadmap.md
- wiki/Agent-Roster.md
- wiki/tasks/WATCHER-next-plan.md

Finish criteria:
Reported ECE is live/non-fixture and held-out, or explicitly null. No promotion language. PR 55 paths untouched.
```

## Completion evidence

- Branch: `cursor/heldout-live-ece-5716`
- Candidate SHA: `b342932`
- Tests: `python3 -m pytest -q` → 318 passed, 3 skipped
- Constitution: unchanged / integrity OK
- PR: https://github.com/MediumThor/Avax-context-engine/pull/62

