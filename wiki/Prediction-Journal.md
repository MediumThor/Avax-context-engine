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

Live persist also catch-up-journals missing closed 5m origins whose h=10 outcome is already known, using `baseline.drift20` only, capped at 24 rows per request. `POST /api/v1/journal/catchup` drains more of the same gap (default 200 per round, max 500; default 20 rounds, max 25) without emitting a quantile or running a loop. Catch-up/drain (and the live drift20 fallback) may attach leakage-safe `empirical_signed_base_rate.v1` P(up) when the sign bucket is large enough; the drift20 point path is unchanged. Null p stays null. Existing quantile rows are not rewritten. Replay and the kill switch write nothing (423 on the drain endpoint). This is not a promotion claim.

The market payload includes `forecast.shadow_journal` with `wrote`, `remaining`, and `model_id`. The workspace Journal panel and health line show those counts when present. Remaining is a coverage gap, not an accuracy score. Replay and the kill switch do not scan remaining; the UI must not treat a zero on those paths as "caught up." The Journal panel can POST `/api/v1/journal/catchup` (drift20 only, 20×200 by default) and then refresh the market payload. That is not a quantile emit and not a promotion.

Live snapshots also insert competing theses into the `theses` table. The same thesis id cannot change `invalidation_fingerprint`. Replay and the kill switch do not insert. `GET /api/v1/theses/{id}` returns the frozen row or 404.

Future candles arriving before the forecast record is durable is a journal failure.

RLH failure must not erase or roll back an already durable ForecastPackage. After the bounded harness latency expires, the Web App may expose the journaled forecast with `harness-degraded` and no fresh explanation. It must never expose an unjournaled LoopTrace.

## Append-only policy

Forecast content cannot be edited after creation. Corrections create a superseding record with reason, never an overwrite.

When horizon h matures, append a ForecastOutcome record linked by forecast ID and h.

`score_journaled_forecasts` reads those outcome rows and the frozen forecast fields. It does not rewrite the forecast. Brier/ECE stay null when `p_close_above_origin` is null. Catch-up rows written after this change may carry empirical P(up) and then score Brier/ECE under the same MIN_BRIER / MIN_ECE gates; older null-p rows stay null. Held-out live ECE still requires `data_source` `binance-vision`/`live`. Point-forecast MAE/RMSE vs `drift20_cum_log_return` / `expected_cum_log_return` are scored once `MIN_MAE` matured pairs exist. Coverage stays null until the interval gate. The live AccuracyPanel prefers those journaled scores when present; otherwise it uses walk-forward slices. `POST /api/v1/journal/catchup` also appends outcomes for horizons already known. This is not a promotion.

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
