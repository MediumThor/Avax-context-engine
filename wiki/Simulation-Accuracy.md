# Simulation and Accuracy

## Purpose

Simulations determine whether the system adds measurable forecasting value. They are not marketing demos.

## Forecast unit

At every eligible 5m close, the system emits one forecast package containing horizons h=1..10. The package is frozen and later scored as each horizon matures.

Research helper `walk_forward_quantiles` scores `freqai.quantiles.research.v1` q50 MAE and empirical q10–q90 coverage against `baseline.zero` and `baseline.drift20` on chronological origins only. It never sets a product promotion flag. Coverage is a hit rate, not ECE.

`walk_forward_probabilities` scores the live `empirical_signed_base_rate.v1` P(up) (Brier) and an empirical residual-vs-drift20 q10–q90 hit rate. Reported ECE is chronological held-out and live/non-fixture only (`binance-vision`). The later 40% of eligible (p, y) pairs is the unseen window; ECE stays null unless that slice has n ≥ 15. Fixture candles, unknown source, and short held-out windows leave `ece` null with `ece_reason`. Those scores are attached to `/api/v1/market` metrics when the walk-forward sample is large enough. They are not a FreqAI-beats-baseline claim. `score_journaled_forecasts` uses the same ECE gate on matured journal rows and stamps `candle_source` on new payloads.

## Core simulations

### 1. Historical walk-forward

Chronologically retrain/evaluate over retained market history. No random shuffle.

Output by horizon:

- cumulative-return MAE/RMSE;
- individual-candle return MAE if modeled;
- direction accuracy;
- Brier score;
- quantile pinball loss;
- q10-q90 coverage;
- maximum favorable/adverse excursion error;
- baseline delta.

### 2. Regime slices

Score independently for:

- bullish trend;
- bearish trend;
- range;
- volatility expansion;
- compression;
- support/resistance proximity;
- BTC-aligned move;
- AVAX/BTC decoupling.

A model that is only useful in one regime should say so.

### 3. Context ablation

Train/evaluate comparable models with:
A. AVAX 5m only;
B. AVAX multi-timeframe;
C. + BTC/ETH cross-market;
D. + Context Engine features;
E. full ensemble.

This measures whether the custom Context Engine actually adds predictive value rather than merely sounding intelligent.

### 4. Pattern ablation

Separately test contributions from:

- structural zones;
- swing state;
- failed-breakout state;
- Fib features;
- pattern hypotheses;
- Elliott candidate features.

Retain only features that improve out-of-sample value or interpretability without unacceptable complexity.

### 5. Historical analog test

For each forecast state, find prior context fingerprints using only information available before the query timestamp. Evaluate whether analog-conditioned statistics improve calibration.

### 6. September 2026 regression replay

Replay the AVAX sequence around the failed ~$8 breakout and subsequent decline.

Measure:

- regime state at each 5m close;
- when bear thesis activates;
- whether a relief rally incorrectly resets `4h`/`1h` state;
- whether invalidation drifts after being triggered;
- model forecast quality through the break;
- harness explanation consistency.

The benchmark does not demand perfect foresight. It demands coherent state discipline and measurable probability quality.

## Simulation modes

### Frozen historical

Model, code and data snapshot are fixed. Used for regression.

### Rolling challenger

Retrain according to production cadence. Used for model selection.

### Shadow-live

Run current and challenger models on incoming live data without affecting UI default. Outcomes score both.

## Baselines

Mandatory baselines:

- no-change price;
- recent drift;
- EMA trend heuristic;
- simple logistic direction model;
- simple linear return model.

Optional external/open-source strategy baselines may be added, but licenses and exact versions must be recorded.

## Statistical caution

Do not overinterpret tiny accuracy differences. Report confidence intervals or bootstrap uncertainty where valid for time-series dependence, and examine stability across windows/regimes.

## Promotion gate example

A challenger may be promoted only if it:

- improves mean Brier score over incumbent by a predefined threshold OR materially improves calibration without unacceptable other degradation;
- does not materially worsen q10-q90 coverage;
- does not materially worsen high-volatility/bear-regime slices;
- beats baseline on enough independent windows;
- passes regression replays;
- meets latency/resource budget.

Exact thresholds live in versioned benchmark configs and must be set before evaluating a candidate.

## Recursive depth ablation

When scoring harness versions, keep Forecast Engine packages frozen and vary only `harness_version` / `max_depth` / halt policy. Metrics and promotion rules: [`Recursive-Evaluation.md`](Recursive-Evaluation.md). Extra loops are not an accuracy claim.

## Reporting

Every simulation emits a machine-readable manifest:

```json
{
  "run_id": "...",
  "commit": "...",
  "data_manifest": "...",
  "feature_schema_version": "...",
  "model_config": "...",
  "windows": [],
  "metrics": {},
  "baselines": {},
  "created_at": "..."
}
```

Web App and wiki summaries must link back to these artifacts.
