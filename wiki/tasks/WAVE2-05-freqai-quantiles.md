# WAVE2-05 — Research-only FreqAI / quantile forecasts

```md
Task: Add a research-only FreqAI/LightGBM-style path that emits next-10 AVAX 5m q10/q50/q90 log-return forecasts without live orders.
Agent: 05
Branch: cursor/wave2-05-freqai-quantiles-9172
Priority: P1
Source main commit: 811ea804aae12f4b42b375ed3307e6fd5cacfd17
Dependency gate: G4 Forecast (challenger payload only; no promotion)

Why:
The Forecast Engine needs a journal-ready quantile challenger for horizons h=1..10. Full FreqAI training is too heavy and flaky for CI. A leakage-safe LightGBM/sklearn wrapper with a tested pure-Python fallback keeps Freqtrade research-only (dry_run, max_open_trades 0, stake 0) and does not claim improvement over Agent 04 baselines.

Inputs:
- CONSTITUTION.md (immutable; no leakage; no fake certainty; no real execution)
- wiki/ML-FreqAI-Directive.md (q10/q50/q90; walk-forward; FreqAI is infrastructure)
- wiki/Data-Contracts.md (ForecastPackage horizon field names)
- wiki/Prediction-Journal.md (journal-ready metadata)
- adapters/freqtrade/* (WAVE2-02 research adapter)
- packages/features/resample.py (completed parents / period_end <= T)
- packages/models/baselines.py (read-only; do not rewrite)

Allowed write scope:
- adapters/freqtrade/**
- packages/models/freqai_quantiles.py
- tests/test_freqai_quantiles.py
- wiki/tasks/WAVE2-05-freqai-quantiles.md
- scripts/bootstrap_freqtrade.sh (only if a research command requires it)

Forbidden write scope:
- CONSTITUTION.md
- services/api/**
- apps/web/**
- packages/models/baselines.py
- packages/models/__init__.py
- real orders, stake > 0, dry_run false
- random-shuffle validation
- fabricated ECE/accuracy

Dependencies:
- Freqtrade pin c064be5325ad6941a2789add795434e6a13dffe9 (WAVE2-02)
- WAVE2-03 completed-parent / period_end visibility (read-only import)
- Honest-slice main 811ea80 (ForecastPackage field names)

Implementation requirements:
1. Keep Freqtrade dry_run true, max_open_trades 0, stake_amount 0, research-only.
2. Implement a leakage-safe quantile regressor wrapper:
   - only closed candles with period_end <= T
   - train only on origins whose h=10 outcome is known at or before T (expanding window)
   - emit h=1..10 q10/q50/q90 cumulative log returns
   - record model_id + feature_schema_version
3. Prefer LightGBM quantile models; fall back to sklearn GradientBoosting quantile; always keep a pure-Python empirical residual-quantile fallback that CI can run without extra wheels.
4. Pin/declare versions. Do not download random wheels in CI.
5. No order-execution surface. No baseline-beating claim. No fabricated ECE/accuracy.
6. Journal-ready payload only (Watcher wires API later).

Acceptance tests:
- command: python3 -m pytest -q tests/test_freqai_quantiles.py
  expected: all tests pass without vendor/freqtrade and without LightGBM
- leakage: mutating candles with period_end > T does not change the forecast at T
- unfinished parent: incomplete 15m/1h buckets and is_closed=false bars are unused
- invariant: q10 <= q50 <= q90 for every horizon
- adapter place_order / execute still raise ResearchOnlyViolation

Metrics gate:
- baseline: none reported
- required result: no accuracy, ECE, or "beats baseline" claim in payload or docs

Historical regressions:
- none in this increment (September 2026 fixture owned elsewhere)

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none (Agent 06 owns walk-forward scoring)
- known failed approaches: full in-CI FreqAI training (too heavy / flaky)

Docs to update:
- wiki/tasks/WAVE2-05-freqai-quantiles.md
- adapters/freqtrade/README.md

Finish criteria:
Research-only quantile path exists, leakage tests green, payload is journal-ready, no live trading path, branch pushed. Watcher opens the PR.
```

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: none
Integration dependency: WAVE2-02 adapter + WAVE2-03 visibility rules already on main

## Status

Implemented on `cursor/wave2-05-freqai-quantiles-9172` from `origin/main` `811ea80`.

## Completion report

### What changed

Added a research-only FreqAI / LightGBM-style path that emits next-10 AVAX 5m quantile forecasts (`q10` / `q50` / `q90` cumulative log returns) without live orders.

- `packages/models/freqai_quantiles.py` trains only on origins whose h=10 outcome is known at or before T, using closed 5m candles with `period_end <= T`.
- Unfinished 15m/1h parents are dropped via WAVE2-03 `completed_parents`.
- Backends: LightGBM quantile (optional), sklearn `GradientBoostingRegressor(loss="quantile")` (optional), pure-Python empirical residual quantiles (always tested).
- `FreqtradeResearchAdapter.emit_research_quantile_forecast` returns a ForecastPackage-shaped journal-ready payload. Order methods still raise `ResearchOnlyViolation`.
- Config remains `dry_run=true`, `max_open_trades=0`, `stake_amount=0`.
- No accuracy, ECE, or baseline-beating claim is produced.

### Exact files changed

- `adapters/freqtrade/AvaxContextStrategy.py`
- `adapters/freqtrade/README.md`
- `adapters/freqtrade/__init__.py`
- `adapters/freqtrade/adapter.py`
- `adapters/freqtrade/constants.py`
- `adapters/freqtrade/quantiles.py` (new)
- `packages/models/freqai_quantiles.py` (new)
- `tests/test_freqai_quantiles.py` (new)
- `wiki/tasks/WAVE2-05-freqai-quantiles.md`

`scripts/bootstrap_freqtrade.sh` was not changed.

### Tests run and results

- `python3 -m pytest -q tests/test_freqai_quantiles.py tests/test_freqtrade_adapter.py tests/test_baselines.py tests/test_journal.py` — **21 passed, 1 skipped** (LightGBM missing in this environment; sklearn backend passed)
- `bash scripts/check_constitution.sh` — Constitution integrity OK
- Adapter `place_order()` / `execute()` / `research_command("trade")` still raise `ResearchOnlyViolation`

### Metrics before/after

| check | before | after |
| --- | --- | --- |
| next-10 q10/q50/q90 research payload | none | journal-ready, ordered |
| future perturbation at T | n/a | forecast unchanged |
| unfinished parent | n/a | unused |
| dry_run / max_open_trades / stake | true / 0 / 0 | unchanged |
| FreqAI beats baselines? | not claimed | still not claimed |
| ECE / accuracy number | none | none |

No out-of-sample score is reported. This increment is not a promotion.

### Known limitations

- Compact feature schema `freqai.quantiles.features.v1` is a placeholder; it does not yet consume the full WAVE2-03 `avax.features.mtf.v1` snapshot.
- LightGBM is optional. CI can run the pure-Python fallback without extra wheels.
- Full FreqAI training / `freqtrade backtesting` is not executed in this increment.
- API / Web App wiring is owned by Watcher later (`services/api/**` and `apps/web/**` were not touched).
- Agent 06 must score this challenger against baselines before any improvement language is allowed.

### Documentation updated

Yes: this contract and `adapters/freqtrade/README.md`. Constitution and ML directive were not edited.

### Contract/schema changed?

Additive only. New model id `freqai.quantiles.research.v1` and feature schema placeholder `freqai.quantiles.features.v1`. ForecastPackage field names match `wiki/Data-Contracts.md`. No shared API schema edit.

### Recommended next task

Agent 06: chronological walk-forward of this payload against Agent 04 baselines. Do not promote. Watcher may later journal the payload through the existing ForecastJournal.
