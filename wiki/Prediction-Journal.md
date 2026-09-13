# Prediction Journal

## Purpose

The Prediction Journal is the audit spine of the system. It prevents hindsight editing and makes model/harness performance measurable.

## Immutable write sequence

At each eligible 5m close:

1. validate source candle completeness;
2. create Context Engine snapshot;
3. assemble feature snapshot;
4. run model ensemble;
5. write ForecastPackage to journal;
6. fsync/commit journal record;
7. only then expose forecast to UI/harness.

Future candles arriving before the forecast record is durable is a journal failure.

## Append-only policy

Forecast content cannot be edited after creation. Corrections create a superseding record with reason, never an overwrite.

When horizon h matures, append a ForecastOutcome record linked by forecast ID and h.

## Required metadata

Each forecast stores:
- forecast ID;
- symbol/timeframe;
- forecast timestamp;
- source data manifest/checksum;
- context snapshot ID;
- feature schema version;
- model ensemble ID and component versions;
- calibration reference;
- application commit SHA;
- upstream Freqtrade commit;
- full horizon outputs;
- data-health state;
- latency metadata.

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
- harness explanation generated at T if present;
- future candles hidden by default;
- outcomes separately revealable.

This is the primary debugging interface for "what did we know then?"

## Evaluation schedule

A 10-horizon package matures incrementally:
- h1 after one closed 5m candle;
- ...
- h10 after ten closed 5m candles.

Outcomes should be scored as soon as each horizon becomes available.

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

Every operator-facing AI analysis should reference the forecast ID and context snapshot ID it used. If the harness is asked later why a forecast was made, it should reconstruct from journal/state rather than invent a retrospective rationale.
