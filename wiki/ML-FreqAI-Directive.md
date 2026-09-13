# ML / FreqAI Directive

## Mission

Use Freqtrade/FreqAI as the quantitative backbone, then extend it with custom leakage-safe context features and a rigorous multi-horizon evaluation layer.

The goal is not to guess an exact candle drawing. The goal is to estimate useful probability distributions for the next 10 five-minute horizons and continuously measure calibration.

## Upstream strategy

Pin an exact Freqtrade commit. Run upstream as a separately identifiable service/dependency rather than copying random source files. Keep an adapter under `adapters/freqtrade/` so upstream upgrades can be tested independently.

Initial reference commit:
`c064be5325ad6941a2789add795434e6a13dffe9`

The bootstrap process should clone the complete upstream repository and checkout the pin. Record the upstream license and commit in generated manifests.

## Initial universe

Required:
- AVAX/USDT 5m
- BTC/USDT 5m
- ETH/USDT 5m

Preferred:
- AVAX/BTC
- BTC dominance or a defensible proxy
- total-market metrics when sourced reliably

Context timeframes:
- 5m
- 15m
- 1h
- 4h
- 1d
- optionally 1w for regime only

## Forecast targets

For every forecast timestamp t, predict horizons h=1..10:

- `log_return_h = log(close[t+h] / close[t])`
- `direction_h = close[t+h] > close[t]`
- cumulative return to horizon h
- future maximum favorable excursion through h
- future maximum adverse excursion through h
- optional high/low quantiles through h
- probability of touching each currently active structural zone through h

Primary output must include quantiles, minimally q10/q50/q90.

## Important target distinction

Do not confuse:
- the return of the individual h-th candle;
- cumulative return from t to t+h;
- path maximum/minimum through t+h.

Store them separately and name them explicitly.

## Features

### Price/return
- returns over 1,2,3,6,12,24,48 candles
- candle body/range/wick ratios
- ATR and realized volatility
- gap to rolling high/low
- rolling skew/kurtosis when stable

### Trend/momentum
- EMA 9/20/50/100/200 distance, slope, ordering
- RSI
- MACD components
- ROC
- ADX / trend-strength metrics

### Volume
- volume z-score
- rolling volume ratio
- OBV or comparable cumulative flow proxy
- volume expansion flag
- price/volume divergence features

### Cross-asset
- BTC/ETH returns across matched windows
- AVAX minus BTC relative return
- rolling beta/correlation
- BTC volatility regime
- synchronized breakout/breakdown flags

### Context Engine features
- regime per timeframe encoded categorically
- distance to nearest support/resistance zone
- zone strength/status/test count
- current swing position
- HH/HL/LH/LL sequence features
- breakout/retest/failure events
- active thesis states
- compression/expansion state
- exact structural Fib distances
- pattern hypotheses encoded as features only after they are leakage-safe

## Leakage rules

Higher-timeframe features may only use completed higher-timeframe candles. Example: at 10:35, the 1h feature set may use the 09:00-09:59 candle and earlier, never the unfinished 10:00-10:59 candle unless explicitly using a separately labeled partial-candle feature.

Confirmed pivots must use `known_at`, not pivot candle timestamp, for feature availability.

All scalers, encoders and model preprocessing must be fit on training data only inside each walk-forward window.

## Model ladder

Every model tier must beat the tier below before promotion.

Tier 0 baselines:
- zero-return
- last return / drift
- EMA direction heuristic

Tier 1 interpretable:
- linear / ridge quantile-style baselines
- logistic direction classifier

Tier 2 tabular:
- LightGBM
- XGBoost
- CatBoost if justified

Tier 3 sequence:
- temporal convolutional network
- LSTM/GRU
- transformer/patch transformer/TFT-type candidates

Tier 4 experimental:
- recurrent/looped transformer approaches as **Forecast Engine** sequence candidates
- multimodel specialist ensembles

The Recursive Learning Harness ([`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md)) is not Tier 4 of the price model. It is the custom explanation / challenge / retrieval loop. A looped transformer may later be *one* `D_φ` implementation, but only as a versioned challenger behind evaluation gates. Do not replace FreqAI numeric heads with an LLM loop.

Do not assume Tier 3/4 beats tabular models.

## Multi-horizon implementation options

Benchmark at least:
1. one model per horizon;
2. one multi-output model;
3. direct quantile models per selected horizons;
4. shared feature encoder with separate horizon heads if sequence models are tested.

## Ensemble

The production forecast should expose individual model outputs plus an ensemble. Candidate weighting methods:
- equal weight among qualified models;
- inverse recent calibrated loss;
- regime-specific historical weighting;
- stacking trained strictly out of sample.

Ensemble weights must not be tuned on the same test window used to report performance.

## Walk-forward design

Initial recommended benchmark:
- minimum 12 months of 5m history, preferably multiple market regimes;
- rolling train window 120-240 days;
- validation window 14-30 days;
- test window 7-14 days;
- step forward chronologically;
- retrain cadence measured realistically.

Run sensitivity analyses rather than declaring one split universally correct.

## Metrics

Regression:
- MAE
- RMSE
- Spearman/rank correlation where useful

Probability:
- Brier score
- log loss
- calibration error
- reliability diagrams

Quantiles:
- pinball loss
- q10-q90 empirical coverage
- interval width

Trading relevance without trading execution:
- sign accuracy conditioned on predicted edge
- MAE of MFE/MAE
- zone-touch probability accuracy
- performance by volatility/regime bucket

## Accuracy claims

Never report a single "accuracy" number without defining the target. UI must distinguish direction accuracy, calibration, return error and interval coverage.

## Continuous retraining

Live retraining is allowed only after:
- data health passes;
- feature schema matches;
- training completes reproducibly;
- challenger beats incumbent on required gates;
- model artifact is versioned;
- watcher approves promotion.

The incumbent stays active if a challenger fails.
