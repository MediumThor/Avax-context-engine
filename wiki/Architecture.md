# Architecture

## Purpose

AVAX Context Engine is a read-only market research and probabilistic forecasting platform. It integrates proven open-source quantitative infrastructure while keeping the Context Engine, Recursive Learning Harness, Evaluation Engine, continuous-improvement loop, and operator experience custom.

The repository currently contains prototypes and stubs for several components below. [`Agent-Build-Plan.md`](Agent-Build-Plan.md) is the current implementation inventory; this page defines accepted boundaries and targets.

## Foundation technology decisions

- Custom services are Python `>=3.11`; CI uses Python 3.12.
- FastAPI + Pydantic own the canonical HTTP/OpenAPI layer.
- The Web App uses the npm workspace, React, TypeScript/TSX, Vite, and TradingView Lightweight Charts.
- Replace all `latest` frontend dependency ranges with reviewed, locked versions before G1 closes.
- SQLite remains valid for deterministic tests and the local prototype. The production persistence target is PostgreSQL for relational records plus a content-addressed filesystem/S3-compatible adapter for immutable payloads; Parquet is for bulk research exports.
- REST serves canonical point-in-time records. Server-Sent Events are the initial one-way live-notification target; clients refetch records by stable ID.
- Docker Compose is the full local orchestration path; fixture mode remains available for fast mobile Web App work.
- TypeScript clients/types derive from accepted schemas rather than hand-maintained copies.

Redis, a distributed broker, Kubernetes, native wrappers, and GPU inference are not foundation requirements. Add them only through an evidence-backed architecture task.

## Top-level components

### 1. Upstream Quant Backbone

Freqtrade/FreqAI is consumed as a pinned upstream dependency/service. We do not casually fork it. We use its data ingestion, feature plumbing, model lifecycle, backtesting and research primitives through an adapter boundary.

Reason: Freqtrade is GPLv3. Keeping it as an independently runnable service/dependency preserves an upgrade path and makes the copyleft boundary explicit. Any direct code copying or linked derivative work must be reviewed for GPL obligations.

Pinned upstream commit: `freqtrade/freqtrade@c064be5325ad6941a2789add795434e6a13dffe9`, recorded in `upstream.lock.json`.

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

Every forecast becomes immutable journal data. When horizons mature, the Evaluation Engine attaches realized outcomes and computes:

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

The Web App is mobile-first React + TypeScript. TradingView Lightweight Charts is the chart renderer. Phone information hierarchy, touch interaction, and loading behavior define the base components; tablet and desktop progressively expose more simultaneous panels without changing route or contract semantics.

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

### 8. Continuous Improvement Workflow

Matured forecasts and LoopTraces become structured evidence. The workflow turns repeated errors into predeclared experiments, bounded agent tasks, reproducible evaluations, and Watcher decisions. It preserves rejected approaches and lessons so later agents receive exact source context rather than a mutable narrative.

See [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md). This workflow may propose changes but cannot bypass the kill switch, tests, Watcher, or `main` verification.

## Repository boundaries

```text
/apps/web                 React/TSX UI
/services/api             FastAPI gateway
/packages/context_engine  deterministic Context Engine core
/packages/market_data     public data and immutable local store
/packages/models          baseline and forecast-model core
/packages/journal         journal core
/packages/evaluator       metric core
/services/harness         recursive learning harness (custom LoopStep)
/packages/contracts/recursive  LoopTrace / EncoderMemory / halt schemas
/services/evaluator       evaluation workflows + reports
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
6. Forecast Engine produces a ForecastPackage for `h=1..10`.
7. The system builds frozen EncoderMemory referencing the accepted context, features, and allocated forecast ID.
8. Prediction Journal durably commits the immutable ForecastPackage and source hashes.
9. RLH runs a bounded LoopStep sequence against that journaled forecast and frozen memory.
10. Prediction Journal durably appends the LoopTrace before any RLH explanation is exposed.
11. Web App refreshes from journaled state, forecast, trace, and health records; a failed RLH degrades the explanation without deleting the forecast.
12. As horizons mature, Evaluation Engine appends outcome records and scores.
13. Continuous-improvement agents inspect aggregate evidence and propose experiments.
14. Watcher decisions and lessons remain retrievable for later agent context packets.

## Architecture constraints

- One canonical timestamp standard: UTC internally.
- Every record knows its source, exchange and symbol mapping.
- Every model output knows its model version and feature schema version.
- Every context snapshot is versioned and replayable.
- Every chart annotation rendered from system state includes provenance.
- Every experiment is reproducible from commit/config/data manifest.
