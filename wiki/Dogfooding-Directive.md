# Dogfooding Directive

## Purpose

The project must be operated on live incoming market data and historical replays so defects are discovered through real use rather than only synthetic tests.

Dogfooding is read-only. No real order execution.

## Daily operating loop

1. Confirm `/health` is green and data freshness is within tolerance.
2. Open AVAX live workspace.
3. Record current higher-timeframe regime and active hypotheses.
4. Inspect the new 10-candle forecast and model disagreement.
5. Confirm the prediction journal stored the forecast before future candles arrive.
6. After horizons mature, inspect realized scoring.
7. Flag material discrepancies between UI explanation and structured state.
8. Convert defects into issues/regression cases.

## Required dogfood questions

At every meaningful move, ask:

- Did the higher-timeframe regime change, or only the 5m state?
- Did an invalidation actually fire?
- Is the UI rendering a real structural zone or an analyst annotation?
- Did model uncertainty expand when models disagreed?
- Was a relief bounce described as a regime reversal without evidence?
- Are predictions improving because of genuine generalization or because the evaluation window changed?
- Did data arrive late or with gaps?

## Forecast diary

Dogfooding should generate an operator diary linked to immutable prediction IDs. Notes may include:
- what surprised the operator;
- what the system emphasized;
- missing context;
- misleading visual hierarchy;
- false certainty;
- useful warnings;
- desired tool query.

Operator notes never alter historical model outputs.

## Defect taxonomy

Tag dogfood findings as:
- `DATA` — bad/missing/stale source data;
- `STATE` — incorrect Context Engine state;
- `MODEL` — forecast/calibration issue;
- `HARNESS` — explanation/reasoning / Recursive Learning Harness loop issue;
- `UI` — presentation/navigation issue;
- `EVAL` — scoring/benchmark issue;
- `OPS` — reliability/observability issue.

## Promotion of mistakes into tests

Any repeated or consequential failure must become one or more of:
- deterministic unit test;
- historical regression replay;
- benchmark slice;
- harness / RLH evaluation fixture under `benchmarks/rlh/`;
- visual regression.

The September 2026 AVAX failed-breakout episode is the founding dogfood regression.

## Continuous monitor

When infrastructure exists, scheduled agents may inspect new matured predictions and open improvement tasks when statistically meaningful drift appears.

Monitor for:
- rolling Brier score deterioration;
- interval undercoverage/overcoverage;
- regime-specific failure;
- systematic bias in up/down probabilities;
- model disagreement spikes;
- stale incumbent model;
- context-state churn;
- data-source gaps;
- `max_depth` becoming the majority halt reason;
- exact-replay canary failures;
- 5m loops describing a higher-timeframe reversal without a ledger event.

Do not retrain or promote solely because one forecast was wrong.

## Weekly review

Generate a weekly evidence report:
- sample counts by horizon;
- direction accuracy by horizon;
- calibration;
- q10-q90 coverage;
- MAE/RMSE;
- baseline deltas;
- regime-sliced results;
- top 10 worst misses;
- top context/harness disagreement cases;
- active experiments;
- incumbent/challenger status.

The Watcher turns that report into prioritized work, not arbitrary model churn.
