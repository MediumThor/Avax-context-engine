# Build Roadmap

## Current status

Several phases have prototype code on `main` (`811ea80`, WAVE-2 integrate + honest slice), but no phase is complete merely because its directory exists. [`Agent-Build-Plan.md`](Agent-Build-Plan.md) is the code-verified inventory and execution order.

| Phase | Gate status on `main` |
| --- | --- |
| 0 — Foundation/governance | In progress: Constitution, RLH schemas, CI, layout, pins |
| 1 — Data/replay | Integrity helpers + snapshot replay + fixture/Binance Vision ingest on `main` |
| 2 — Context Engine | Pivots/zones/regime/patterns/cross-market/analogs + live snapshot theses with frozen invalidation + zone lifecycle in `build_snapshot` + insert-only journaled theses (this branch) |
| 3 — Forecasting | Journaled next-10 quantiles + walk-forward vs drift20 on `main` (`80a4d70`); challenger now training on `avax.features.mtf.v1` (this branch, not promoted) |
| 4 — Journal/evaluation | Journal + walk-forward baseline MAE; this branch adds walk-forward Brier/ECE/coverage for empirical P(up) and residual q10–q90 when n is sufficient. Not a promotion claim. |
| 5 — RLH | EncoderMemory / LoopStep / challenge / SWA / probes on `main`; live forecast journals first, runs a bounded loop, then appends LoopTrace without rewriting the forecast. `/loops/run` remains a stub |
| 6 — Web App | ForecastFan / overlays / AccuracyPanel mounted; fan draws only when q10/q50/q90 are journaled |
| 7-10 | Not complete |

Honest slice on `main` (`811ea80`):

1. Market page reads real Binance Vision candles or the September 2026 fixture. It never labels fixture/stale data `LIVE`.
2. Forecasts are journaled before outcomes. When enough matured train origins exist, `p_close_above_origin` is an empirical signed base rate (`empirical_signed_base_rate.v1`), not a fabricated confidence percentage. Outcomes append later without rewriting the forecast row.
3. Reported baseline numbers are walk-forward only, with `sample_count`. Zero-model direction abstains.
4. Replay `?as_of=` / `/api/v1/replay/{symbol}` hides later candles. The 5m relief bounce must not flip 4H.

This branch additionally journals leakage-safe empirical q10/q50/q90 (research model id `freqai.quantiles.research.v1`) when enough history exists, plus the MTF feature snapshot. It does **not** claim the challenger beats drift20.

Agent 00 updates status only after tests pass on an accepted `main` SHA.

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

Finish gate: canonical contracts, locked foundation versions, CI, task/lock coordination, and the repository skeleton are accepted on `main`; agents can work without inventing interfaces.

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
- mobile-first TSX app shell
- Lightweight Charts candlesticks/volume
- structural zones
- timeframe context rail
- forecast fan
- thesis panel
- replay mode
- accuracy/calibration dashboard
- health/system pages
- phone-first 360px/390px validation followed by tablet/desktop progressive enhancement

Finish gate: the operator can complete the market/context/forecast/thesis/replay loop on a phone without opening raw logs; larger layouts progressively enhance the same routes and contracts.

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
2. create evidence-linked learning candidates and bounded hypotheses;
3. deploy competing research agents from accepted task contracts;
4. benchmark challengers, including RLH depth ablation;
5. watcher reviews evidence under [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md);
6. promote only qualified improvements;
7. add regressions for consequential failures.

Do not raise `max_depth` because a research tweet said "infinite reasoning depth." RLT itself defines infinite depth as an extensible temporal path, not infinite work per token.

Follow [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md): predeclare evaluation, preserve rejected lessons, and verify every accepted change on `main`.

## Agent execution

[`Agent-Build-Plan.md`](Agent-Build-Plan.md) is authoritative for dependency gates, whole-product waves, and write ownership. [`Agent-Roster.md`](Agent-Roster.md) and Watcher artifacts are authoritative for currently active work. [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md) applies specifically to the active RLH implementation; it is not a whole-product launch order.
