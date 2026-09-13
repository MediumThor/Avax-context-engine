# Architecture

## Purpose

AVAX Context Engine is a read-only market research and probabilistic forecasting platform. It integrates proven open-source quant infrastructure while keeping the context model, state model, AI harness, evaluation loop and user experience custom.

## Top-level components

### 1. Upstream Quant Backbone

Freqtrade/FreqAI is consumed as a pinned upstream dependency/service. We do not casually fork it. We use its data ingestion, feature plumbing, model lifecycle, backtesting and research primitives through an adapter boundary.

Reason: Freqtrade is GPLv3. Keeping it as an independently runnable service/dependency preserves an upgrade path and makes the copyleft boundary explicit. Any direct code copying or linked derivative work must be reviewed for GPL obligations.

Pinned initial upstream target: `freqtrade/freqtrade@c064be5325ad6941a2789add795434e6a13dffe9` (develop snapshot observed 2026-09-13).

### 2. Data Service

Responsibilities:

- acquire AVAXUSDT, BTCUSDT, ETHUSDT and AVAXBTC if available;
- normalize exchange timestamps, symbols and candle boundaries;
- persist raw immutable candle data;
- derive higher-timeframe candles from closed lower-timeframe candles without lookahead;
- expose freshness, gaps and checksum metadata;
- later ingest funding/open interest/liquidation/order-book data.

### 3. Context Engine

The custom Context Engine converts observations into persistent structured market state.

It owns:

- regime per timeframe;
- swing structure;
- validated support/resistance zones;
- volatility state;
- relative-strength state;
- breakout/retest/failure events;
- pattern hypotheses;
- thesis ledger and invalidations;
- state-transition audit log.

It is deterministic where possible. AI explanation may interpret state but may not silently mutate state.

### 4. Forecast Engine

The Forecast Engine combines:

- FreqAI models;
- simple baselines;
- custom tabular models;
- optional sequence models after baseline proof;
- Context Engine features;
- cross-market features.

It outputs horizons +1 through +10 five-minute candles as distributions, not exact prophecies.

### 5. Internal AI Harness / Recursive Learning Harness

The custom harness reads structured data through tools. It does not receive screenshots as its primary source of truth.

It is specified as a **Recursive Learning Harness**: a causal encoder (Context Engine + leakage-safe features) plus an all-token recurrent `LoopStep` that uses the same transition for observed facts and generated reasoning. See [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

Tools expose:

- market state snapshot;
- time series query;
- structural zones;
- thesis ledger;
- model ensemble outputs;
- historical analogs;
- prediction journal performance;
- current data health;
- loop state / cite / halt.

The harness produces concise explanations, challenge/counter-thesis analysis and operator summaries. It may propose experiments, never falsify measured confidence. Every production loop is budgeted, halted, and journaled as a `LoopTrace` before outcomes are known.

### 6. Evaluation Engine

Every forecast becomes immutable journal data. When horizons mature, the evaluator attaches realized outcomes and computes:

- return MAE/RMSE;
- direction accuracy;
- Brier score;
- log loss where appropriate;
- quantile pinball loss;
- interval coverage;
- calibration curves;
- max favorable/adverse excursion error;
- regime-sliced metrics;
- baseline deltas.

### 7. Web App

React + TypeScript. TradingView Lightweight Charts is the chart rendering library.

The UI consumes our API and renders:

- candles and volume;
- structural zones with provenance;
- timeframe regime ribbon;
- hypotheses and invalidations;
- 10-candle forecast fan/bands;
- model disagreement;
- calibration and recent accuracy;
- state change timeline;
- journal replay.

No trade execution in v1.

## Recommended repository layout

```text
/apps/web                 React/TSX UI
/services/api             FastAPI gateway
/services/context         deterministic context engine
/services/harness         recursive learning harness (custom LoopStep)
/packages/contracts/recursive  LoopTrace / EncoderMemory / halt schemas
/services/evaluator       prediction scoring + reports
/adapters/freqtrade       Freqtrade/FreqAI integration
/packages/contracts       JSON/Pydantic/TS schemas
/packages/market-math     shared structural math
/infra                    Docker compose, CI, observability
/scripts                  bootstrap, data, simulation tools
/tests                    cross-service + regression suites
/wiki                     agent-operable project memory
/benchmarks               immutable benchmark manifests
/data/manifests           data checksums/metadata only
```

## Data flow

1. Candle closes at exchange.
2. Data service validates and writes immutable raw event.
3. Higher timeframes update only when their candle closes.
4. Context Engine processes state transition.
5. Feature assembler builds leakage-safe feature snapshot.
6. Forecast Engine produces horizon distributions.
7. Context Engine + Recursive Learning Harness produce a journaled `LoopTrace` from frozen `EncoderMemory`.
8. Prediction journal writes forecast **and** loop trace before next candle outcome.
9. UI refreshes.
10. As horizons mature, evaluator appends outcome scores.
11. Continuous-improvement agents inspect aggregate evidence and propose experiments.

## Architecture constraints

- One canonical timestamp standard: UTC internally.
- Every record knows its source, exchange and symbol mapping.
- Every model output knows its model version and feature schema version.
- Every context snapshot is versioned and replayable.
- Every chart annotation rendered from system state includes provenance.
- Every experiment is reproducible from commit/config/data manifest.
