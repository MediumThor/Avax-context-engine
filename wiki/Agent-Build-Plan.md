# Agent Build Plan

## Goal

Turn the current prototype into one integrated, runnable AVAX product on `main` without overlapping writes, invented interfaces, or parallel product histories.

`main` is the only durable source of truth. Every agent starts from the latest `main`; accepted work is verified there. Temporary worktrees or branches are conflict-isolation tools only and must be reconciled immediately or discarded.

## Current `main` baseline

The repository is no longer documentation-only. It contains a tested prototype spine, but the presence of a module does not mean its phase gate is complete.

| Area | Present on `main` | Still required for its gate |
| --- | --- | --- |
| Governance | Constitution, agent rules, Watcher artifacts, task contracts, kill switch | Keep roster/status synchronized with accepted main SHAs |
| Data | Binance public fetch/store helpers and tests | Canonical manifests, gaps/duplicates, durable raw store, deterministic replay API, full source policy |
| Context | Indicator, resampling, pivot/zone lifecycle in `build_snapshot`, parent-child, leakage-safe snapshot analogs, sealed Sept dump, competing snapshot theses, insert-only journaled thesis invalidation | Versioned transitions / full fingerprint remain incomplete |
| Forecast | Baseline helpers, FreqAI adapter/config, evaluator metrics, held-out live ECE (null on fixture) | Canonical feature/forecast contracts, walk-forward runner, quantile promotion (still lost to drift20), model ensemble, reproducible manifests |
| Journal | SQLite forecast/outcome prototype plus append-only `loop_traces`, insert-only `theses`, and capped drift20 shadow catch-up of mature-able 5m origins | Every 5m close still not filled in one request; production storage adapter |
| Recursive harness | EncoderMemory / LoopStep / challenge / SWA / probes; live forecast journals first, RETRIEVEs analog.search + theses, then appends LoopTrace; `/loops/run` retries that loop on a journaled forecast | Evaluation of extra depth; no extra quantile emit on the request path |
| API | FastAPI health/system/kill-switch and loop-run stub | Typed market/context/forecast/journal/evaluation/replay APIs and generated client |
| Web App | React/Vite prototype chart and kill-switch shell | Mobile-first workspace, live typed data, bottom sheet/navigation, overlays, forecast fan, replay, accuracy, health states |
| Operations | Compose/CI/bootstrap prototypes | Reproducible full stack, persistent services, migrations, observability, clean recovery, release checks |

Update this table only from verified code/tests on `main`.

## Mainline protocol

1. Agent 00 checks the operator kill switch and active-task registry.
2. Agent 00 assigns one bounded task, exact write scope, dependencies, and acceptance commands.
3. The task starts from the recorded current `main` SHA.
4. Direct `main` work is allowed only with an exclusive path lock and serialized writes. Otherwise use a disposable isolated worktree/branch.
5. The agent implements, tests, documents, and reports the exact result commit.
6. Agent 00 reviews scope and evidence, reconciles onto the newest `main` if needed, and reruns critical checks there.
7. Accepted work remains on `main`; rejected work is reverted/quarantined and recorded without weakening tests.
8. New dependent tasks start only after the accepted main SHA and contract versions are recorded.

Never create long-lived feature, foundation, staging, or integration branches. When two accepted changes conflict, serialize them against the newest `main`.

## Interface gates

| Gate | Required accepted output | Unlocks |
| --- | --- | --- |
| G0 Governance | Mainline protocol, kill switch, task/lock registry, Constitution check | Agent work |
| G1 Contracts | Canonical core Pydantic/OpenAPI models, recursive JSON schemas, generated TypeScript types, contract tests | Service and Web App integration |
| G2 Data | Normalized immutable candles, manifests, fixtures, replay clock, health | Context and feature work |
| G3 Context | Versioned snapshots, fingerprints, zones, hypotheses, transitions, deterministic replay | Context features, overlays, analogs, harness encoder |
| G4 Forecast | Feature snapshots, baselines, ForecastPackage, atomic journal path | Quant challengers and forecast UI |
| G5 Evaluation | Walk-forward manifests, calibration, regime slices, frozen promotion plans | Accuracy UI and promotion |
| G6 Product | Mobile-first workspace, API, RLH, replay, health/degraded states | Integrated QA and shadow-live |
| G7 Improvement | Evidence cases, experiment records, agent context packets, promotion/lesson records | Continuous evidence-gated improvement |

If an upstream gate changes, dependent work stops until the owner versions the contract and Agent 00 accepts it on `main`.

## Execution waves

Parallelize only tasks with accepted inputs and non-overlapping paths. A lane appearing more than once receives a new contract each time.

### Active Wave R — Recursive Learning Harness

Follow [`Agent-Roster.md`](Agent-Roster.md), [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md), and the live Watcher artifacts. Do not launch duplicate lanes. Complete schemas, EncoderMemory, LoopStep, challenge, SWA, evaluator, and leakage work against the existing RLH contracts.

Gate: recursive contract tests pass; required fixtures run; exact replay and halt invariants hold; accepted work is verified on `main`.

### Product Wave 1 — Core contracts and reproducible shell

- Agent 31: canonical non-RLH Pydantic/OpenAPI contracts plus generated TypeScript types.
- Agent 32: one clean-checkout full-stack command and fixture mode.
- Agent 33: docs/link/contract checks and complete Python/Web App CI.
- Agent 34: typed health, structured logging, and freshness contracts.
- Agent 17: mobile-first design system and fixture shell at 360px/390px.

Gate: G1 plus a reproducible fixture-mode Web App on `main`.

### Product Wave 2 — Data and chart foundations

- Agent 01: public data ingestion, immutable manifests/store, gaps/duplicates, and deterministic fixtures.
- Agent 02: pinned Freqtrade/FreqAI adapter and reproducible bootstrap.
- Agent 10: confirmed pivots and swing sequence.
- Agent 14: timestamp-aligned BTC/ETH/AVAXBTC context.
- Agent 18: touch-safe Lightweight Charts wrapper.

Gate: G2; primitive outputs conform to G1 and pass point-in-time leakage tests.

### Product Wave 3 — Persistent Context Engine

- Agent 11: structural-zone lifecycle and provenance.
- Agent 12: confirmed-anchor Fibonacci/measured-move features.
- Agent 09: hierarchical `1w`/`1d`/`4h`/`1h`/`15m`/`5m` regime state.
- Agent 13: competing pattern/Elliott hypotheses.
- Agent 15: versioned thesis ledger and immutable invalidation.
- Agent 16: snapshots, fingerprints, transitions, and deterministic replay.
- Agent 19: typed overlays after accepted fixtures exist.

Gate: G3 and the September 2026 failed-breakout regression pass on `main`.

### Product Wave 4 — Forecast and evaluation spine

- Agent 03: leakage-safe feature snapshots.
- Agent 04: mandatory baselines.
- Agent 06: chronological walk-forward Evaluation Engine and run manifests.
- Agent 35: evaluation plans, experiment registry, promotion decisions, and lessons.
- Agent 36: independent leakage attacks.

After baseline/evaluator acceptance:

- Agent 05: FreqAI/tabular ensemble challengers.
- Agent 07: calibration and interval validation.

Gate: G4/G5 with reproducible out-of-sample artifacts. A challenger building successfully is not a promotion.

### Product Wave 5 — Mobile operator intelligence

- Agent 31: complete accepted API surface and regenerate client types.
- Agents 20-22: forecast fan, performance views, phone navigation, and loop inspector.
- Agents 25-29: connect the accepted RLH to real journaled context/forecast records.

Gate: G6; the complete operator loop works at 360px/390px before desktop enhancement is accepted.

### Product Wave 6 — Independent QA and shadow-live

- Agent 23: touch, keyboard, accessibility, and performance.
- Agent 24: phone-first visual QA, then tablet/desktop.
- Agent 30: harness hallucination/hierarchy tests.
- Agent 37: journal and replay verification.
- Agent 38: dogfooding and evidence capture.
- Agent 39: clean-checkout benchmark replication.

Gate: release checks pass from a clean checkout of `main`, followed by read-only shadow-live operation.

### Product Wave 7 — Continuous improvement

Use [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md). Mature outcomes, create evidence-linked candidates, freeze evaluation plans, launch bounded tasks, preserve rejected lessons, and promote only Watcher-approved results onto `main`.

Gate: G7 completes at least one reproducible accepted or rejected improvement cycle.

## Default write ownership

Task contracts must narrow these scopes to exact files/subtrees. Shared schemas have one writer per batch.

| Lane | Default scope |
| --- | --- |
| 01 | `packages/market_data/`, data scripts/tests/docs |
| 02 | `adapters/freqtrade/`, `upstream.lock.json`, bootstrap tests/docs |
| 03-05 | Assigned feature/baseline/model subtrees under `packages/models/` or accepted Forecast Engine paths |
| 06-07 | Assigned evaluator/calibration subtrees and tests |
| 09-16 | Assigned `packages/context_engine/` subtrees and tests |
| 17-24 | Assigned `apps/web/` components/routes/tests; Agent 17 owns shared tokens/primitives |
| 25 | `packages/contracts/recursive/` and generated RLH schema bindings for its active batch |
| 26-29 | Sequentially assigned `services/harness/` subtrees and tests |
| 30 | `services/evaluator/rlh/`, `tests/rlh/`, assigned fixtures |
| 31 | `services/api/` and canonical non-RLH shared contracts; coordinate with Agent 25 for RLH schemas |
| 32-34 | Exact environment, CI, or observability files assigned by Agent 00 |
| 35 | Benchmark/evaluation-plan and continuous-improvement records/workflow |
| 36-39 | Independent QA tests/artifacts; production fixes require a separate correction task |

An agent needing a shared contract change submits it to the current contract owner and stops coding against the imagined interface. An agent finding a test defect submits evidence to Agent 00 and does not weaken the gate inside its feature change.

## Definition of built

A clean checkout of `main` must be able to:

1. start the documented stack and fixture mode;
2. ingest or replay validated AVAX/BTC/ETH data;
3. rebuild multi-timeframe context deterministically;
4. durably journal and later score `h=1..10` forecasts plus any associated LoopTraces, without losing a forecast when RLH degrades;
5. compare models honestly against frozen baselines and evaluation plans;
6. explain context through the read-only RLH without inventing evidence;
7. provide the complete mobile-first operator workflow;
8. expose health, stale, degraded, replay, and kill-switch states;
9. pass the permanent September 2026 regression and leakage suites;
10. turn measured failures into retrievable, evidence-gated improvements.
