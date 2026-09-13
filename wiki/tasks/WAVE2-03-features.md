# WAVE2-03 — Leakage-safe feature assembler

```md
Task: Implement a leakage-safe AVAX 5m feature assembler with completed 15m/1h/4h/1d context, BTC/ETH relative features, and EMA/RSI/ATR/volume features.
Agent: 03
Branch: cursor/wave2-03-features-2cfd
Priority: P1

Why:
Forecast inputs must be versioned and free of future-data leakage. Higher-timeframe and cross-market features may only use information knowable at timestamp T.

Inputs:
- CONSTITUTION.md
- wiki/ML-FreqAI-Directive.md
- wiki/Data-Contracts.md
- wiki/Testing-Directive.md
- packages/context_engine/indicators.py (read/reuse when present)
- packages/context_engine/resample.py (read/reuse when present)

Allowed write scope:
- packages/features/**
- tests/features/**
- wiki/tasks/WAVE2-03-features.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- services/harness/**
- apps/web/**
- services/api/**
- packages/models/baselines.py
- packages/journal/journal.py
- packages/context_engine/engine.py
- packages/market_data/store.py
- real trade execution

Dependencies:
- Candle OHLC semantics from Data-Contracts
- Optional import of context_engine indicators/resample (same algorithms vendored as fallbacks so this package is testable on main)

Implementation requirements:
1. Versioned feature schema (`feature_schema_version` string).
2. Higher-timeframe features use only completed parent candles at T.
3. Track availability timestamps / `known_at` per timeframe and on the snapshot.
4. Tests: perturb candles after T and prove the snapshot at T is unchanged; unfinished parent candles must not leak.
5. Do not train production models. Do not claim accuracy.
6. Reuse context_engine indicators/resample when importable.

Acceptance tests:
- command: python -m pytest -q tests/features
  expected: all tests pass
- leakage: mutating any bar whose period ends after T does not change values or availability at T
- unfinished parent: 15m/1h/4h/1d bars still open at T never enter HTF features

Metrics gate:
- baseline: none (no model training)
- required result: no accuracy claims; schema + leakage tests only

Historical regressions:
- none in this increment (September 2026 fixture is owned by context/data agents)

Docs to update:
- wiki/tasks/WAVE2-03-features.md

Finish criteria:
Feature assembler exists, schema is versioned, HTF/cross-asset features are leakage-safe, tests are green, branch is pushed.
```

## Status

Implemented on `cursor/wave2-03-features-2cfd`. Tests green.

## Completion report

### What changed

Leakage-safe feature assembler for AVAX 5m plus completed 15m/1h/4h/1d context, BTC/ETH relative features, and EMA/RSI/ATR/volume inputs. Snapshots are versioned (`feature_schema_version = avax.features.mtf.v1`) and record per-timeframe `known_at` availability. A bar is visible at T only when it is closed and its period end is `<= T`. Incomplete parent buckets are dropped. No models are trained.

When `packages.context_engine` is importable, EMA/RSI/ATR/realized-vol and `resample_closed` are reused; otherwise identical fallbacks in `packages/features/_lib.py` are used so the package is testable on current main.

### Exact files changed

- `packages/features/__init__.py`
- `packages/features/_lib.py`
- `packages/features/assembler.py`
- `packages/features/indicators.py`
- `packages/features/relative.py`
- `packages/features/resample.py`
- `packages/features/schema.py`
- `packages/features/types.py`
- `tests/features/conftest.py`
- `tests/features/test_assembler.py`
- `tests/features/test_context_engine_reuse.py`
- `tests/features/test_indicators.py`
- `tests/features/test_feature_leakage.py`
- `tests/features/test_relative.py`
- `tests/features/test_resample.py`
- `tests/features/test_schema.py`
- `tests/features/test_unfinished_parent.py`
- `wiki/tasks/WAVE2-03-features.md`

### Tests run

```
PYTHONPATH=. python -m pytest -q tests/features
```

- without context_engine: **32 passed, 2 skipped** (reuse tests skip)
- with context_engine on PYTHONPATH: **34 passed**

### Metrics before/after

Not applicable. No model training, no accuracy claims, no walk-forward scores.

### Known limitations

- Input is 5m OHLCV only; Context Engine regime/zone/thesis features are not encoded yet.
- HTF indicators share 5m spans (EMA 200 on 1d needs 200 completed days).
- Rolling corr/beta use a fixed 24-bar window on aligned closes; gaps drop that timestamp from the intersection.
- Fallback copies of context_engine math will need a version bump if those upstream functions change.
- This branch is rooted at current GitHub `main` (wiki/constitution). Integrators merging onto the scaffold/watcher tree should take only `packages/features/**`, `tests/features/**`, and this task file.

### Documentation updated

- `wiki/tasks/WAVE2-03-features.md` (contract + this report)

### Contract/schema change

Yes: new feature schema `avax.features.mtf.v1` (additive package; does not mutate existing API contracts).

### Recommended next task

Agent 04 / forecast path: consume `FeatureSnapshot` as the journaled feature payload (schema version + values + availability) and keep target columns out of the feature matrix. Agent 36 can add extra leakage red-team cases against this assembler.
