# Build Roadmap

## Phase 0 — Foundation and governance

Deliverables:
- Constitution
- AGENTS protocol
- full subsystem wiki
- Watcher directive
- repository layout
- typed core contracts
- CI skeleton
- Freqtrade/FreqAI upstream pin/bootstrap

Finish gate: agents can be launched independently without inventing architecture.

## Phase 1 — Data and replay

Deliverables:
- public exchange OHLCV ingestion
- normalized candle storage
- resampling to 15m/1h/4h/1d/1w
- gap/duplicate detection
- historical replay API
- data manifests/checksums

Finish gate: a date range can be replayed deterministically with no lookahead.

## Phase 2 — Context Engine v1

Deliverables:
- swing/pivot engine
- structural zones
- regime state machine
- breakout/retest/failure events
- volatility state
- cross-market BTC context
- thesis ledger
- state-transition log
- September 2026 regression fixture

Finish gate: state rebuild is deterministic and founding regression passes.

## Phase 3 — FreqAI + baseline forecasting

Deliverables:
- upstream Freqtrade bootstrap pinned to exact commit
- adapter API
- FreqAI config for AVAX/BTC/ETH and multi-timeframe features
- zero/drift/EMA/logistic baselines
- LightGBM/XGBoost candidates
- direct horizons 1..10
- q10/q50/q90 or equivalent uncertainty outputs

Finish gate: full walk-forward run with reproducible artifacts and no leakage.

## Phase 4 — Prediction journal + evaluator

Deliverables:
- append-only forecast packages
- incremental horizon outcomes
- calibration/scoring engine
- baseline comparison
- regime slicing
- immutable run manifests

Finish gate: every forecast can be replayed and independently scored.

## Phase 5 — Internal AI Harness / Recursive Learning Harness

Deliverables:
- structured tool layer
- frozen `EncoderMemory` before any decoder step
- one `LoopStep` transition for ingest and emit
- Context KV + recurrent state + SWA memory banks
- mandatory halt budget and typed halt reasons
- bull/bear challenge step
- forecast explanation contract
- journaled `LoopTrace` bound to each `ForecastPackage`
- historical analog query
- exact vs current-policy replay
- hallucination/regression + depth-ablation suite

Directive: [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md). Launch contracts: [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md).

Finish gate: harness explanations are traceable to state/forecast IDs, live and replay hashes match on fixtures, and loops never invent unsupported levels/probabilities.

## Phase 6 — React/TradingView UI

Deliverables:
- TSX app shell
- Lightweight Charts candlesticks/volume
- structural zones
- timeframe context rail
- forecast fan
- thesis panel
- replay mode
- accuracy/calibration dashboard
- health/system pages
- mobile responsive pass

Finish gate: operator can understand market state, uncertainty and performance without opening raw logs.

## Phase 7 — Simulation tournament

Run multiple approaches against frozen benchmarks:
- baseline-only
- FreqAI default-style tabular
- custom context features
- ensemble
- sequence candidates
- analog-conditioned candidates

Perform ablations of context features and pattern modules.

Finish gate: production candidate selected on predeclared out-of-sample metrics, not visual appeal.

## Phase 8 — UI/UX pass

Independent agents review:
- information hierarchy
- chart legibility
- mobile usability
- navigation
- accessibility
- stale/error states
- operator cognitive load

No model logic changes in UI-pass branches.

## Phase 9 — Shadow-live living system

Deliverables:
- live read-only data
- continuous forecasts
- journal maturation
- rolling accuracy reports
- incumbent/challenger shadow runs
- drift detection
- Watcher improvement queue

Finish gate: system runs continuously for a meaningful sample period without journal gaps and produces weekly evidence reports.

## Phase 10 — Continuous improvement

Loop forever:
1. observe errors/drift **and** loop process failures (halt mix, replay mismatch, false reversals);
2. generate bounded hypotheses;
3. deploy competing research agents from [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md);
4. benchmark challengers, including RLH depth ablation;
5. watcher reviews evidence under [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md);
6. promote only qualified improvements;
7. add regressions for consequential failures.

Do not raise `max_depth` because a research tweet said "infinite reasoning depth." RLT itself defines infinite depth as an extensible temporal path, not infinite work per token.

## Initial parallel agent batch after foundation

Recommended first 16 agents:

- 01 data ingestion
- 02 Freqtrade bootstrap/adapter
- 03 feature schema
- 04 baseline models
- 06 walk-forward runner
- 09 regime state machine
- 10 pivot engine
- 11 zone clustering
- 14 BTC cross-market context
- 15 thesis ledger
- 17 web shell/design tokens
- 18 Lightweight Charts wrapper
- 25 AI tool contracts
- 31 FastAPI/OpenAPI contracts
- 33 CI/reproducibility
- 36 leakage red-team

Agent 00 watches the entire batch.
