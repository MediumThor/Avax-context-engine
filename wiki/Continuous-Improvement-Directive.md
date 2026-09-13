# Continuous Improvement Directive

## Mission

Build a system that improves its AVAX context, forecasts, and Recursive Learning Harness from measured outcomes without rewriting history, leaking future data, or promoting plausible-sounding changes without evidence.

This directive governs evidence-to-code improvement. The per-forecast recurrent reasoning architecture is separately defined in [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md). A deeper reasoning loop is not itself a software or model promotion.

Continuous improvement has two coupled loops:

1. **Market-context loop** — every closed candle updates versioned, multi-timeframe state and preserves what the system knew at each forecast timestamp.
2. **System-improvement loop** — matured forecast outcomes create structured error cases, bounded experiment proposals, reproducible evaluations, and Watcher-approved promotions.

Neither loop may directly self-modify production behavior. Agents work from the latest `main` under exclusive path locks or in disposable isolation; accepted changes exist only after Watcher verification on `main`.

## Durable memory layers

The system must preserve distinct sources of truth:

| Layer | Contents | Mutation rule |
| --- | --- | --- |
| Observations | Raw candles and source metadata | Append-only |
| Context | State snapshots, transitions, zones, hypotheses | New versions; no historical overwrite |
| Forecast experience | Forecast packages and RLH LoopTraces | Append-only, content-addressed |
| Outcomes | Matured horizon results and scores | Append linked records |
| Research | Error cases, experiments, manifests, metrics | Versioned and reproducible |
| Decisions | Promotion/rejection rationale and regression links | Append-only audit record |
| Agent lessons | Generalizable implementation failures and fixes | Versioned; evidence-linked |

Mutable prose summaries may help retrieval but cannot replace these records.

## Learning cycle

1. Journal a forecast before outcomes exist.
2. Append outcomes as each horizon matures.
3. Recompute global and regime-sliced metrics from journal records.
4. Detect a repeated error, drift signal, calibration failure, operability defect, or context/harness disagreement.
5. Create a `LearningCandidate` linked to exact evidence.
6. Predeclare the proposed change, affected contracts, comparison baseline, evaluation windows, metrics, and rejection conditions.
7. Assign a bounded task contract and exclusive path lock; use a registered disposable work surface only when isolation is required.
8. Implement and test without changing the frozen evaluation definition.
9. Run chronology-safe walk-forward, regression, leakage, and operational checks.
10. Have Agent 00 approve, reject, or quarantine the candidate.
11. Integrate accepted work into current `main`, verify it there, and append a `PromotionDecision`.
12. Convert consequential failures into permanent tests, benchmark slices, or replay fixtures.

One wrong forecast is evidence to inspect, not sufficient evidence to retrain or change behavior.

## Learning candidate contract

Every candidate conforms to [`LearningCandidate`](Data-Contracts.md#learningcandidate). It links the observed failure to exact forecasts, context snapshots, baseline runs, and a predeclared evaluation plan. Its lifecycle is `proposed -> assigned -> testing -> accepted|rejected|quarantined`, with `superseded` available when a later candidate replaces it. Lifecycle transitions are versioned or append-only events.

## Error taxonomy

Use the shared dogfooding categories:

- `DATA` — source integrity, alignment, freshness, or normalization;
- `STATE` — incorrect or unstable Context Engine state;
- `MODEL` — forecast, calibration, drift, or ensemble behavior;
- `HARNESS` — unsupported explanation, retrieval, or hierarchy failure;
- `UI` — misleading or inaccessible presentation;
- `EVAL` — scoring, split, baseline, or benchmark defect;
- `OPS` — reliability, latency, health, or reproducibility.

Attach regime, horizon, volatility, data-health, and model-version dimensions when applicable. Do not reduce failures to unstructured chat transcripts.

## Chronology and evaluation isolation

Continuous improvement creates an elevated leakage risk. Enforce all of the following:

- Discovery outcomes may motivate a candidate but cannot also serve as the candidate's only unseen proof.
- Preprocessing, calibration, model selection, and ensemble weights fit inside training/development windows only.
- Promotion windows and gates are declared before candidate results are inspected.
- Once a sealed promotion window influences implementation decisions, mark it consumed for future final-claim purposes or version the evaluation plan with a genuinely unseen window.
- Live shadow forecasts remain immutable and are scored exactly as originally emitted.
- Evaluation code changes receive independent review when they affect a candidate's score.

## Context packets for agents

Before work begins, the orchestrator assembles a bounded context packet containing:

- task contract and dependency versions;
- Constitution hash and relevant directives;
- accepted API/schema versions;
- exact source commit and allowed write scope;
- linked error cases and forecast/context IDs;
- frozen evaluation plan and baseline run IDs;
- applicable regression fixtures;
- known failed approaches and why they failed;
- required commands and finish criteria.

Agents retrieve source records by ID instead of relying on a lossy summary. Completion reports append new evidence and limitations to the packet; they do not rewrite earlier evidence.

## Promotion decision evidence

Every accepted, rejected, or quarantined candidate produces a [`PromotionDecision`](Data-Contracts.md#promotiondecision) backed by:

- candidate and task IDs;
- source and result commit SHAs;
- data/config/schema/model hashes;
- commands and run manifests;
- before/after metrics with uncertainty and sample counts;
- regime-sliced regressions;
- leakage and historical replay results;
- operational cost/latency change;
- decision, reviewer, rationale, and follow-up;
- new regression or lesson IDs.

When approaches are statistically indistinguishable, prefer the simpler, faster, and more interpretable implementation.

## Continuous-improvement acceptance criteria

The first complete loop exists when the repository can:

1. reconstruct what was known at a historical AVAX forecast timestamp;
2. append its realized outcomes without mutating the forecast;
3. generate a structured error case from measured evidence;
4. launch a bounded experiment with a frozen evaluation plan;
5. reproduce its metrics from recorded manifests;
6. record a Watcher decision;
7. merge an accepted improvement into `main` or preserve a rejected lesson;
8. retrieve that evidence in a later agent context packet.
