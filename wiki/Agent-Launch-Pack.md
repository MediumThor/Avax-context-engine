# Agent Launch Pack

Use this page to launch the first autonomous Cursor agent batch. Every agent must read `CONSTITUTION.md`, `AGENTS.md`, `wiki/Home.md`, and its subsystem directive before touching code. Agent 00 remains the Watcher and must monitor all branches.

## Agent 00 — Watcher / integrator

**Prompt:**

> You are Agent 00, Watcher for AVAX Context Engine. Read CONSTITUTION.md, AGENTS.md, wiki/Watcher-Directive.md, wiki/Agent-Orchestration.md, and all task contracts. Do not primarily implement features. Continuously inspect active agent branches, enforce non-overlapping write scopes, rerun critical tests, detect lookahead leakage, reject undocumented schema drift, compare claimed model gains against frozen baselines, and reprompt agents with bounded corrections. Maintain the integration queue. Never modify the Constitution. No real trade execution is allowed. The founding regression is the September 2026 failed ~$8 AVAX breakout and subsequent decline; protect higher-timeframe state from lower-timeframe narrative drift.

## Agent 01 — Data ingestion

> Build public read-only exchange OHLCV ingestion for AVAX/USDT, BTC/USDT, ETH/USDT at 5m. Normalize UTC timestamps, detect gaps/duplicates, persist immutable raw candles and create data manifests/checksums. Allowed scope: services/data, packages/contracts data schemas, tests/data, related wiki. Do not modify model logic, UI, Constitution or benchmark definitions. Finish when a historical range can be fetched/imported, validated, persisted and replayed deterministically with tests.

## Agent 02 — Freqtrade/FreqAI backbone

> Integrate the complete pinned Freqtrade repository specified in upstream.lock.json through the adapters/freqtrade boundary. Preserve GPL notices and upgradeability. Implement repeatable bootstrap, data-download/backtest commands, FreqAI config and a read-only multi-horizon AVAX research path. No order execution. Do not fork upstream unless required and documented. Finish when the pinned upstream can be bootstrapped and a dry/backtest pipeline can emit model predictions for our adapter contracts.

## Agent 03 — Feature schema

> Define and implement leakage-safe feature assembly for AVAX 5m plus 15m/1h/4h/1d context, BTC/ETH correlated features, EMA/RSI/ATR/volume/relative-strength features and Context Engine features. Track feature availability timestamps. Write perturb-future leakage tests. Do not train production models. Finish with versioned feature schema and deterministic feature snapshots.

## Agent 04 — Baseline models

> Implement zero-return, drift, EMA heuristic, linear return and logistic direction baselines for horizons 1..10. Use chronology-safe fit/evaluation only. Produce common ForecastPackage outputs and benchmark artifacts. No deep models. Finish when every future challenger has a reproducible baseline to beat.

## Agent 05 — FreqAI model ensemble

> Implement LightGBM/XGBoost/FreqAI model candidates for direct horizons 1..10 and quantile/uncertainty outputs where supported. Expose component-model outputs and ensemble output. Do not claim improvement until Agent 06 walk-forward evaluation passes. Preserve read-only execution state.

## Agent 06 — Walk-forward simulator

> Build the canonical chronological walk-forward evaluator described in wiki/Simulation-Accuracy.md. No random shuffle. Score MAE/RMSE, direction accuracy, Brier, pinball loss, interval coverage, MFE/MAE and baseline deltas by horizon/regime. Emit immutable run manifests. Keep evaluator independent from model implementation.

## Agent 07 — Calibration / uncertainty

> Implement probability calibration and forecast interval validation without using test-window outcomes to fit the same reported test window. Add reliability diagrams/data, expected calibration error, interval coverage and abstention/disagreement metrics. Finish when UI can consume calibrated quality metadata.

## Agent 08 — OSS research scout

> Survey maintained open-source ML/time-series/crypto research projects that can improve data, features, evaluation, drift detection or model training. Record license, exact version, maintenance status, purpose and integration boundary before recommending dependencies. Never add dependencies merely because they are popular.

## Agent 09 — Regime engine

> Implement the versioned multi-timeframe regime state machine for 1W/1D/4H/1H/15m/5m with hysteresis, parent/child semantics and deterministic replay. Lower-timeframe moves cannot silently reset higher-timeframe state. Build regression tests around the September 2026 AVAX breakdown.

## Agent 10 — Pivot / swing engine

> Implement and compare at least two leakage-safe confirmed-pivot methods, including known_at timestamps. Produce HH/HL/LH/LL structure and benchmark sensitivity. Never expose a pivot before it was knowable in real time.

## Agent 11 — Structural zones

> Build reproducible support/resistance zone clustering from swing reactions, tests and optional volume evidence. Zones are ranges with provenance/status/test count, not arbitrary lines. Implement probe/penetration/acceptance/reclaim lifecycle and tests.

## Agent 12 — Fib / measured move

> Build exact structural Fibonacci retracement/extension features using confirmed swing anchors with timestamp provenance. Never infer anchors from pixel geometry. Treat Fib as contextual evidence, not guaranteed support. Add tests proving future pivot information is unavailable early.

## Agent 13 — Pattern hypotheses

> Implement pattern hypotheses as competing scored objects: continuation, flags, wedges/triangles, compression, failed breakouts, accumulation/distribution and optional Elliott candidates. Every hypothesis has evidence, counter-evidence, confirmation and immutable invalidation. Do not turn subjective pattern names into unconditional truth.

## Agent 14 — Cross-market context

> Build BTC/ETH/AVAXBTC relative-strength and rolling correlation/beta/volatility context. Detect synchronized/decoupled moves and expose features/state to Context Engine and forecast models. Align timestamps exactly and test gaps.

## Agent 15 — Thesis ledger

> Implement immutable-versioned bull/bear thesis objects. Once invalidation triggers, close the thesis; do not move its invalidation. Changed reasoning creates a new thesis version. Add transition/audit tests and API contracts.

## Agent 16 — State replay

> Build deterministic Context Engine snapshot persistence and historical replay. Given raw candles + engine version, reproduce the same transition sequence. Expose point-in-time `what was known then` queries for UI and AI harness.

## Agent 17 — Web shell / design system

> Build the React/TSX application shell following wiki/UI-Directive.md. Establish responsive grid, design tokens, loading/error/stale states and accessible primitives. Do not invent market metrics or touch model logic.

## Agent 18 — TradingView chart

> Build the Lightweight Charts wrapper with candles, volume, EMA layers, resize cleanup and typed overlay APIs. Prepare primitives for structural zones, pivots and forecast fan. No trading/order UI.

## Agent 19 — Context overlays

> Render structural zones, pivot/state-change markers, breakout/retest events and provenance inspection. System-derived structures and analyst annotations must be visually distinct.

## Agent 20 — Forecast fan

> Render next-10-candle q10/q50/q90 forecast envelopes, median path, per-horizon probability and model disagreement. Never draw one deterministic future candle path as certainty.

## Agent 21 — Accuracy dashboard

> Build model performance views by horizon/regime with sample count, baseline comparison, Brier/calibration, interval coverage and return error. A generic undefined `accuracy` badge is forbidden.

## Agent 22 — Navigation/mobile

> Implement routes and mobile behavior from wiki/Navigation-Directive.md. Preserve symbol/timeframe state, make replay mode unmistakable, and ensure no hover-only controls on mobile.

## Agent 23 — Accessibility/performance

> Audit keyboard access, responsive chart behavior, listener cleanup, render performance and accessible metric labels. Do not alter model or context semantics.

## Agent 24 — Visual QA

> Independently review UI against wiki/UI-Directive.md with mobile/tablet/desktop captures and visual regression tests. Open bounded correction tasks; do not redesign data semantics.

## Agent 25 — AI tool contracts

> Implement the custom Internal AI Harness tools defined in wiki/AI-Harness-Directive.md. The model must query structured state/forecast/evaluation data, not screenshots as primary truth. Tools are read-only.

## Agent 26 — Context retrieval

> Implement point-in-time context retrieval and recent transition summaries for the harness. Preserve source IDs/provenance. Never synthesize levels not present in Context Engine state.

## Agent 27 — Explanation planner

> Build structured analysis output separating measured facts, model forecast and interpretation. Require regime, what changed, what did not change, bull/bear evidence, invalidations, health and confidence provenance.

## Agent 28 — Counter-thesis critic

> Build the mandatory challenge step that attacks the primary synthesis: check invalidations, higher-timeframe conflicts, arbitrary levels, uncalibrated confidence and future leakage. Store critic result with analysis snapshot.

## Agent 29 — Harness memory

> Build harness memory around snapshot IDs, hypothesis versions, transitions, model versions and operator annotations. Mutable prose summaries cannot be the sole source of truth.

## Agent 30 — AI harness evaluation

> Build historical snapshot tests for regime respect, invalidation discipline, no invented support, faithful probability communication and `no thesis change` behavior. Red-team hallucinations.

## Agent 31 — API/OpenAPI contracts

> Build FastAPI endpoints and canonical Pydantic/OpenAPI contracts for candles, snapshots, zones, forecasts, journal, metrics and health. Generate TypeScript client/types where practical.

## Agent 32 — Dev environment

> Make one documented local command boot the stack. Implement Docker/dev fixtures, .env.example and Freqtrade bootstrap integration. No secrets, no real trading keys.

## Agent 33 — CI/reproducibility

> Enforce Python tests, web build/typecheck, Constitution hash, leakage suite, regression smoke and reproducibility manifests in CI. Never weaken a gate in the same change that fails it without independent review.

## Agent 34 — Observability/data health

> Implement structured logging, data freshness/gap metrics, model age, journal health, service health and aggregate `/health`. UI must know when forecasts are stale/degraded.

## Agent 35 — Benchmark registry

> Build immutable benchmark/run manifests with commit/config/data hashes and predeclared promotion gates. Evaluation definitions are versioned independently from candidate models.

## Agent 36 — Leakage red team

> Attempt to prove future leakage by perturbing future candles, partial higher-timeframe candles, pivot confirmation, train/test scalers, feature expansion and target columns. Fail builds on leakage.

## Agent 37 — Forecast replay red team

> Select historical periods and independently replay prediction packages/outcomes. Verify journal immutability and that reported metrics recompute exactly.

## Agent 38 — Dogfood operator

> Use live/read-only and replay views as an operator. Convert confusing or misleading behavior into tagged DATA/STATE/MODEL/HARNESS/UI/EVAL/OPS issues and regression tests.

## Agent 39 — Independent benchmark replication

> Re-run promotion candidates from clean checkout and frozen manifests. Compare hashes/metrics and report any non-reproducibility to Agent 00. Do not share implementation work with model authors during replication.
