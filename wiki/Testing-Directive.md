# Testing Directive

## Philosophy

The project fails if it is impressive but not falsifiable. Tests must cover market-data correctness, context-state logic, model leakage, forecast scoring, UI contracts and historical regressions.

## Test layers

### Unit tests

Cover deterministic functions:

- candle resampling;
- EMA/indicator features;
- pivot confirmation timing;
- support-zone clustering;
- breakout/acceptance state machine;
- thesis invalidation;
- forecast metric calculations;
- serialization/schema validation.

### Property tests

Use generated data to assert invariants:

- resampling preserves OHLC semantics;
- future candles cannot change features at earlier timestamps;
- zone bounds remain ordered;
- state replay is deterministic;
- Prediction Journal records are immutable;
- quantiles remain ordered q10 <= q50 <= q90.

### Leakage tests

Leakage tests are mandatory and blocking.

Examples:

- perturb candles after timestamp T and prove features/forecast inputs at T do not change;
- compare higher-timeframe features before/after an unfinished parent candle closes;
- verify pivot `known_at` behavior;
- verify scalers fit only inside training windows;
- verify target columns never enter feature matrices.

### Integration tests

Cover:

- data -> context state;
- context -> feature snapshot;
- feature snapshot -> forecast;
- forecast -> journal;
- matured prediction -> Evaluation Engine;
- API -> typed web client;
- fixture replay -> chart overlays.

### Historical regression tests

Maintain benchmark scenarios with raw source data plus expected structural events, not hand-edited chart screenshots.

Permanent case: September 2026 AVAX failed breakout.

Expected broad sequence:

- recovery into ~$8 region;
- repeated failure near ~$8.15-$8.20;
- deterioration/loss of ~$8 support;
- bearish structure remains active through relief bounces unless explicit reclaim criteria are met;
- system must not continuously move bullish invalidation lower.

Regression tests should assert state transitions rather than require exact hindsight-perfect trade calls.

Add a symmetric hierarchy case in which the 4h/1d regime is bullish while 5m/15m turns bearish. The system may represent a tactical retracement hypothesis, but must not label a higher-timeframe bearish reversal before its predefined confirmation triggers.

### Model tests

Every model training job runs:

- schema check;
- NaN/inf check;
- chronology check;
- train/validation/test boundary check;
- baseline comparison;
- calibration evaluation;
- regime-sliced evaluation;
- reproducibility check on a sample window.

### Recursive Learning Harness tests

Mandatory once `services/harness` exists; schema tests are mandatory now:

- `python3 tests/contracts/test_recursive_schemas.py`
- live vs exact-replay hash match;
- future-candle perturbation does not change `encoder_memory_hash` or `LoopTrace` at `T`;
- 5m steps cannot mutate 4H encoder slices;
- `CHALLENGE` present on directional synthesis;
- countertrend hypotheses remain tactical until higher-timeframe reversal confirmation;
- halt reason is typed and always present;
- invented zone / invented probability / uncalibrated percent fixtures fail;
- measured facts, forecasts, and interpretation remain distinguishable;
- an immaterial 5m candle can produce `NO_CHANGE`;
- September 2026 parent-regime fixture.

See [`Recursive-Evaluation.md`](Recursive-Evaluation.md) and [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

### UI tests

Required:

- component tests for metric displays;
- typed fixture contract tests;
- Playwright/e2e navigation;
- visual regression for chart overlays where stable;
- 360px and 390px phone viewport tests before tablet/desktop cases;
- touch pan/crosshair/page-scroll conflict tests;
- stale/error/loading states;
- accessibility checks.

### Continuous-improvement workflow tests

Required cases include:

- a learning candidate cannot exist without source evidence and a predeclared evaluation plan;
- a sealed evaluation plan cannot be changed by the candidate evaluated against it;
- discovery records do not appear in the candidate's unseen promotion window;
- rejected and quarantined lessons remain retrievable in later context packets;
- promotion decisions reproduce from referenced manifests and commits;
- no agent workflow can promote directly to production behavior without Watcher and `main` integration gates.

## Simulation tiers

### Smoke

Small deterministic fixture; seconds/minutes. Runs every PR.

### Standard

Several historical windows across regimes. Runs on integration candidates.

### Full

Large walk-forward sweep over all retained history and model candidates. Runs on model promotion or scheduled research cycles.

## Metric locks

For each production model family, store expected benchmark ranges. A new change that degrades key metrics beyond tolerance fails unless explicitly classified as an experiment.

Never lower metric gates in the same change whose model fails them without independent review.

## Accuracy reporting test

Any API/UI field named `accuracy` must include or resolve to:

- metric definition;
- horizon;
- date/window;
- sample count;
- baseline value.

Otherwise the test should fail.

## Test ownership

Feature authors write tests, but agents 36-39 independently attempt to break them. Watcher decides whether evidence is sufficient.
