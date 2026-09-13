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

Implemented on `cursor/wave2-03-features-2cfd`. See completion report at the bottom of this file after tests.
