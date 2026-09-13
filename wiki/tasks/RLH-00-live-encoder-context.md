# RLH-00 — Live EncoderMemory + analog.search on journaled forecasts

```md
Task: After a forecast is journaled, freeze EncoderMemory from the live snapshot and run one bounded loop that can call analog.search / context.get_hypotheses on that snapshot only.
Agent: 00
Branch: cursor/encoder-live-context-8771
Priority: P0
Source main commit: 77b6eee
Dependency gate: G4/G6 (journal + snapshot analogs/theses already on main)

Why:
The product loop requires EncoderMemory and a LoopTrace after ForecastPackage commit. analog.search and theses existed on the snapshot and as unused tools; the live forecast path never bound them. RLH must read the same frozen context as the journal, without rewriting the forecast or claiming confidence.

Inputs:
- wiki/Recursive-Learning-Harness.md
- wiki/Recursive-Loop-Spec.md
- wiki/AI-Harness-Directive.md
- packages/contracts/recursive/encoder-memory.schema.json
- packages/context_engine/analogs.py
- packages/context_engine/snapshot_theses.py

Allowed write scope:
- services/harness/encoder/**
- services/harness/loop/runner.py
- services/api/runtime.py
- tests/harness/encoder/**
- tests/test_rlh_live_context.py
- tests/test_honest_slice.py
- tests/test_kill_switch.py
- tests/test_live_quantile_journal.py
- apps/web/src/**
- wiki/tasks/RLH-00-live-encoder-context.md
- wiki/Agent-Build-Plan.md
- wiki/Build-Roadmap.md
- wiki/Recursive-Learning-Harness.md
- wiki/Recursive-Learning-Contracts.md
- wiki/AI-Harness-Directive.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py
- packages/context_engine writes / mutations

Implementation requirements:
1. Journal the forecast payload first. Do not mutate it after emit.
2. build_encoder_memory fills zone_ids / hypothesis_ids from the snapshot.
3. EncoderTools.analogs / hypotheses come from snapshot_analogs / snapshot_theses (known_at normalized to Z).
4. run_loop RETRIEVE calls analog.search / context.get_hypotheses only when those lists are non-empty (preserve existing hashes).
5. Kill switch skips the loop; POST /api/v1/loops/run stays a stub and still returns 423.
6. UI shows halt reason, analog count, hypothesis ids — not confidence.
7. LoopTraces are not persisted this increment.

Acceptance tests:
- encoder ids + analog.search from September fixture snapshot
- analog.search refuses known_at > as_of
- live forecast wrapper includes loop summary; forecast payload unchanged
- future-candle perturbation still hash-stable
- kill switch skips loop and still 423s /loops/run
- existing loop exact-replay hashes still match

Metrics gate:
- none (no promotion, no fabricated accuracy)

Historical regressions:
- September 2026 4H bear invalidation remains frozen
- honest drift20 / residual quantile path unchanged

Docs to update:
- Agent-Build-Plan, Build-Roadmap, Recursive-Learning-Harness, Recursive-Learning-Contracts, AI-Harness-Directive

Finish criteria:
Live forecast journals first, then a bounded loop reads frozen snapshot analogs and theses. Tests pass. No schema change. No confidence claims.
```
