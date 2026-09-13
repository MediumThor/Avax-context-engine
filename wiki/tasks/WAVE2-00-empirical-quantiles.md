# WAVE2-00 — Journaled empirical next-10 quantiles

```md
Task: Wire leakage-safe next-10 q10/q50/q90 forecasts into the live API journal path and attach avax.features.mtf.v1 snapshots.
Agent: 00
Branch: cursor/empirical-quantiles-8771
Priority: P0
Source main commit: 811ea804aae12f4b42b375ed3307e6fd5cacfd17
Dependency gate: G4 Forecast (challenger journaled; not promoted)

Why:
Agent 05 produced a research-only quantile emitter. The live PrototypeRuntime still journals only honest drift20 point paths, so ForecastFan cannot draw a distribution and the journal column still says feature schema "1". The product loop requires a journaled next-10 distribution written before outcomes, plus the MTF feature snapshot known at T.

Inputs:
- CONSTITUTION.md (no leakage, no fake certainty, no live orders)
- wiki/ML-FreqAI-Directive.md
- wiki/Prediction-Journal.md
- packages/models/freqai_quantiles.py (WAVE2-05)
- packages/features (avax.features.mtf.v1)
- services/api/runtime.py
- apps/web ForecastFan (reads q10/q50/q90_cum_return)

Allowed write scope:
- services/api/runtime.py
- packages/models/freqai_quantiles.py (additive aliases only)
- packages/models/__init__.py
- packages/journal/journal.py (return feature_schema_version)
- apps/web/src/api/types.ts
- apps/web/src/components/ForecastFan.tsx
- apps/web/src/App.tsx
- tests/test_live_quantile_journal.py
- wiki/tasks/WAVE2-00-empirical-quantiles.md
- wiki/tasks/WAVE2-00-watch.md
- wiki/Build-Roadmap.md
- wiki/Prediction-Journal.md
- artifacts/watcher/**

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py
- real orders / dry_run false
- fabricated ECE / accuracy / "beats baseline"

Implementation requirements:
1. Prefer emit_quantile_forecast on a bounded lookback; fall back to emit_baseline_forecast on InsufficientHistory.
2. Attach simple-return aliases exp(q)-1 so ForecastFan can draw an envelope.
3. Assemble packages.features at forecast time and journal feature_schema_version=avax.features.mtf.v1 with the snapshot.
4. Keep p_close_above_origin null. No promotion language.
5. Future candles after T must not change the journaled payload at T.

Acceptance tests:
- command: python3 -m pytest -q tests/test_live_quantile_journal.py tests/test_freqai_quantiles.py tests/test_honest_slice.py
  expected: pass
- q10 <= q50 <= q90; simple aliases match exp(log)-1
- mutating bars with period_end > T does not change the forecast at T
- journal feature_schema_version is avax.features.mtf.v1 when a snapshot exists

Metrics gate:
- baseline: none claimed
- required result: no accuracy / ECE / baseline-beating claim

Finish criteria:
Live /api/v1/market forecast journals a next-10 distribution (or honest drift20 fallback), MTF features, leakage tests green, PR opened.
```

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: none
Integration dependency: WAVE2-05 on this branch (4728493); main 811ea80
