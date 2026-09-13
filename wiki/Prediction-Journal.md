# Prediction Journal

## Purpose

The Prediction Journal is the audit spine of the system. It prevents hindsight editing and makes model/harness performance measurable.

## Immutable write sequence

At each eligible 5m close:

1. validate source candle completeness;
2. create Context Engine snapshot;
3. assemble feature snapshot;
4. run model ensemble;
5. build frozen EncoderMemory with the allocated forecast ID;
6. durably commit ForecastPackage plus its source/context/feature/encoder hashes;
7. run the bounded Recursive Learning Harness against that frozen memory;
8. durably append `LoopTrace` before exposing an RLH explanation;
9. expose the forecast and, when present, its journaled explanation to the Web App.

Current live path journals the ForecastPackage, runs one bounded loop, then appends the LoopTrace to `loop_traces` linked by forecast id. The forecast `payload_json` / `payload_sha256` are not updated. Replay (`persist=False`) still runs the loop in memory but does not store a trace. `GET /api/v1/loops/{id}` reads the stored row. `POST /api/v1/loops/run` attaches another bounded loop to a journaled forecast only; it does not emit or rewrite a ForecastPackage.

Live snapshots also insert competing theses into the `theses` table. The same thesis id cannot change `invalidation_fingerprint`. Replay and the kill switch do not insert. `GET /api/v1/theses/{id}` returns the frozen row or 404.

Future candles arriving before the forecast record is durable is a journal failure.

RLH failure must not erase or roll back an already durable ForecastPackage. After the bounded harness latency expires, the Web App may expose the journaled forecast with `harness-degraded` and no fresh explanation. It must never expose an unjournaled LoopTrace.

## Append-only policy

Forecast content cannot be edited after creation. Corrections create a superseding record with reason, never an overwrite.

When horizon h matures, append a ForecastOutcome record linked by forecast ID and h.

`score_journaled_forecasts` reads those outcome rows and the frozen forecast probabilities. It does not rewrite the forecast. Brier/ECE/coverage stay null until the minimum sample gates in `packages/models/probability_walkforward.py` are met. The live AccuracyPanel prefers those journaled scores when present; otherwise it uses `walk_forward_probabilities`.

## Required metadata

Each forecast stores:

- forecast ID;
- symbol/timeframe;
- forecast timestamp;
- source data manifest/checksum;
- context snapshot ID;
- feature schema version (`avax.features.mtf.v1` on the live prototype when `assemble_features` succeeds);
- optional `mtf_feature_snapshot` blob (point-in-time assembler output, journaled with the forecast);
- model ensemble ID and component versions;
- calibration reference;
- application commit SHA;
- upstream Freqtrade commit;
- full horizon outputs;
- data-health state;
- latency metadata;
- zero or more linked `loop_trace_id` values when the Recursive Learning Harness ran.

## Storage design

Recommended:

- relational DB for queryable metadata/outcomes;
- immutable object/blob representation for complete forecast package;
- content hash stored in relational row;
- optional parquet export for bulk analysis.

Do not rely only on mutable application logs.

## Replay

The replay API must retrieve:

- market observations known at time T;
- Context Engine snapshot at T;
- model forecast written at T;
- `LoopTrace` generated at T if present (preferred over unjournaled prose);
- future candles hidden by default;
- outcomes separately revealable.

This is the primary debugging interface for "what did we know then?"

## Evaluation schedule

A 10-horizon package matures incrementally:

- h1 after one closed 5m candle;
- ...
- h10 after ten closed 5m candles.

Outcomes should be scored as soon as each horizon becomes available.

The live prototype (`mature_outcomes`) appends those rows without rewriting the forecast payload or hash. Replay `as_of` may only mature horizons whose close is known at that timestamp. A persist also journals the origin 10 bars earlier so h=1..10 can mature on the same request.

## Journal integrity tests

- mutate future candles and confirm prior forecast package hash is unchanged;
- attempt duplicate forecast for same symbol/base timeframe/timestamp/model ensemble and enforce deterministic policy;
- validate monotonic outcome maturation;
- verify forecast payload hashes;
- simulate process restart between model output and UI publication;
- simulate DB/object-store partial failure and ensure forecast is not falsely reported as journaled.

## Research access

Model-development agents may query journal history but must use chronology-safe splits. A model trained on journal outcomes cannot be evaluated on those same records as unseen performance.

## Harness linkage

Every operator-facing AI analysis should reference the forecast ID, context snapshot ID, and `loop_trace_id` it used. If the harness is asked later why a forecast was made, it should reconstruct through [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md) replay rather than invent a retrospective rationale.

`LoopTrace` is append-only. Corrections create a new trace with `supersedes`, never an overwrite. `LoopOutcome` attaches later.
