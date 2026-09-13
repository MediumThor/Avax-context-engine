# Data Contracts

> **Status:** RLH JSON schemas under `packages/contracts/recursive/` are implemented and tested. The non-RLH examples below are target contracts; current `packages/context_engine` dataclasses and SQLite records are prototype shapes, not the completed canonical Pydantic/OpenAPI layer.

## Principles

Contracts are versioned, typed and explicit. Services communicate through schemas, not undocumented dictionaries.

Internal timestamps are UTC ISO-8601 or Unix epoch milliseconds. Candle boundaries are aligned to exchange/server time after normalization. Symbols/timeframes follow [`Documentation-Standards.md`](Documentation-Standards.md).

## Candle

```json
{
  "symbol": "AVAXUSDT",
  "timeframe": "5m",
  "exchange": "binance",
  "open_time": "2026-09-13T09:00:00Z",
  "close_time": "2026-09-13T09:04:59.999Z",
  "open": 7.25,
  "high": 7.29,
  "low": 7.23,
  "close": 7.27,
  "volume": 123456.7,
  "is_closed": true,
  "received_at": "...",
  "source_id": "..."
}
```

No feature pipeline may treat a record with `is_closed=false` as closed. Any feature derived from an unfinished candle requires an explicitly named partial-candle namespace and point-in-time leakage tests; RLH ignores partial parent candles in v1.

## MarketStateSnapshot

```json
{
  "id": "snapshot-id",
  "symbol": "AVAXUSDT",
  "as_of": "...",
  "schema_version": "1",
  "engine_version": "...",
  "previous_snapshot_id": null,
  "data_manifest_id": "...",
  "source_data_hash": "sha256:...",
  "timeframes": {
    "4h": {
      "regime": "bearish",
      "swing_state": "LH_LL",
      "volatility": "expanded",
      "nearest_support_ids": [],
      "nearest_resistance_ids": [],
      "last_transition_id": "..."
    }
  },
  "cross_market": {},
  "active_hypothesis_ids": [],
  "transition_ids": [],
  "context_fingerprint_id": "...",
  "health": "valid",
  "built_at": "...",
  "analogs": [
    {
      "origin_close_time": "...",
      "distance": 0.0,
      "realized_h10_log_return": 0.0,
      "known_at": "...",
      "note": "Analog outcome known at T. Not a forecast and not confidence."
    }
  ],
  "pattern_hypotheses": [],
  "fib_levels": []
}
```

## ContextFingerprint

```json
{
  "id": "context-fingerprint-id",
  "schema_version": "1",
  "snapshot_id": "snapshot-id",
  "symbol": "AVAXUSDT",
  "as_of": "...",
  "values": {
    "regime_4h": "bearish",
    "distance_to_support_atr": 0.6,
    "btc_alignment": -0.4
  },
  "availability": {
    "regime_4h": "...",
    "distance_to_support_atr": "...",
    "btc_alignment": "..."
  }
}
```

Fingerprint keys/types are governed by `schema_version`. Every availability timestamp is at or before `as_of`.

## FeatureSnapshot

```json
{
  "id": "feature-snapshot-id",
  "schema_version": "1",
  "symbol": "AVAXUSDT",
  "base_timeframe": "5m",
  "as_of": "...",
  "data_manifest_id": "...",
  "context_snapshot_id": "snapshot-id",
  "context_fingerprint_id": "context-fingerprint-id",
  "values": {},
  "availability": {},
  "content_hash": "sha256:..."
}
```

Feature snapshots are immutable model inputs. Target columns never appear in `values`.

## StructuralZone

```json
{
  "id": "...",
  "symbol": "AVAXUSDT",
  "lower": 7.15,
  "upper": 7.35,
  "role": "support",
  "status": "active",
  "timeframes": ["1d", "4h"],
  "sources": [],
  "strength": 0.73,
  "test_count": 2,
  "created_at": "...",
  "known_at": "...",
  "last_test_at": "...",
  "provenance": {}
}
```

Current snapshot rows also carry `interaction` and `outcome` from `ZoneTracker`. Role is assigned at formation `known_at`. Strength is evidence weight, not a calibrated percent.

## Hypothesis

```json
{
  "id": "...",
  "lineage_id": "...",
  "symbol": "AVAXUSDT",
  "direction": "bear",
  "kind": "failed_breakout_continuation",
  "regime_relation": "aligned",
  "status": "active",
  "created_at": "...",
  "known_at": "...",
  "context_snapshot_id": "...",
  "evidence": [],
  "counter_evidence": [],
  "confirmation_rules": [],
  "invalidation_rules": [],
  "closed_at": null,
  "closure_reason": null,
  "version": 1
}
```

Allowed `regime_relation` values are `aligned`, `countertrend`, `mixed`, and `unknown`.

Hypotheses are immutable versions. New material evidence or parent-regime alignment creates a new version within the same lineage. Invalidation rules may not move across active versions; changed invalidation reasoning closes the old lineage and starts a new one.

Live snapshot theses are also stored append-only in the journal `theses` table keyed by thesis id. `sync_theses` inserts the first payload and refuses a later write that would change `invalidation_fingerprint`. Replay does not insert. This is journal storage, not a Recursive Learning schema change.

## ForecastPackage

```json
{
  "id": "...",
  "schema_version": "1",
  "symbol": "AVAXUSDT",
  "base_timeframe": "5m",
  "forecasted_at": "...",
  "created_at": "...",
  "origin_close": 7.27,
  "context_snapshot_id": "...",
  "feature_snapshot_id": "...",
  "model_ensemble_id": "...",
  "feature_schema_version": "...",
  "data_manifest_id": "...",
  "source_data_hash": "sha256:...",
  "application_commit": "...",
  "upstream_freqtrade_commit": "...",
  "horizons": [
    {
      "h": 1,
      "expected_cum_log_return": 0.0,
      "p_close_above_origin": 0.5,
      "q10_cum_log_return": -0.01,
      "q50_cum_log_return": 0.0,
      "q90_cum_log_return": 0.01,
      "expected_max_favorable_excursion": 0.0,
      "expected_max_adverse_excursion": 0.0,
      "zone_touch_probabilities": {}
    }
  ],
  "component_models": [],
  "calibration_ref": "...",
  "health": "valid"
}
```

Allowed `health` values are `valid`, `degraded`, `stale`, and `unknown`. Return fields in this example are cumulative log returns from the forecast-origin close. Simple or individual-candle returns require distinct names. Web App price bands are derived from the origin and quantiles.

## ForecastOutcome

```json
{
  "forecast_id": "...",
  "schema_version": "1",
  "h": 1,
  "matured_at": "...",
  "realized_cum_log_return": 0.0,
  "realized_close_above_origin": true,
  "realized_max_favorable_excursion": 0.0,
  "realized_max_adverse_excursion": 0.0,
  "scores": {
    "abs_error": 0.0,
    "brier": 0.0,
    "pinball_q10": 0.0,
    "pinball_q50": 0.0,
    "pinball_q90": 0.0
  }
}
```

Outcomes attach to forecasts; forecasts are never mutated.

Use MAE only for **mean absolute error**. Write maximum adverse excursion in full or as `max_adverse_excursion`.

## StateTransition

```json
{
  "id": "...",
  "symbol": "AVAXUSDT",
  "timeframe": "1h",
  "observed_at": "...",
  "known_at": "...",
  "entity": "regime",
  "from": "neutral",
  "to": "bearish",
  "causes": [],
  "input_snapshot_hash": "sha256:..."
}
```

## Recursive Learning Harness

Loop contracts (`EncoderMemory`, `RecurrentState`, `LoopStep`, `LoopTrace`, `HaltDecision`, `ReplayPackage`, `LoopOutcome`) are specified in [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md) and versioned as JSON Schema under `packages/contracts/recursive/`.

They attach to `MarketStateSnapshot` and `ForecastPackage` by ID. They never overwrite those records.

## Continuous-improvement contracts

These target records are owned by Agent 35 with shared-schema review by Agent 31. They are not yet implemented machine schemas.

### EvaluationPlan

A sealed plan identifies data manifests, chronology-preserving split policy, baselines, metrics, regime slices, promotion gates, and regression fixtures. Its lifecycle is `draft -> sealed -> consumed|retired`; a candidate may not modify the sealed plan used to judge it.

### LearningCandidate

A versioned candidate links an observed `DATA|STATE|MODEL|HARNESS|UI|EVAL|OPS` failure to exact forecast, snapshot, LoopTrace, baseline-run, and EvaluationPlan IDs. Its lifecycle is `proposed -> assigned -> testing -> accepted|rejected|quarantined`, with `superseded` available. It is a hypothesis, not a conclusion.

### PromotionDecision

An append-only decision links candidate/task IDs, source and accepted `main` SHAs, evaluation/regression manifests, reviewer, rationale, and follow-up. Allowed decisions are `accepted`, `rejected`, and `quarantined`.

### LessonRecord

A versioned lesson contains a concise summary, applicability scope, and mandatory evidence IDs. New evidence appends or supersedes a lesson; it never erases the earlier record.

## API versioning

Expose contracts under `/api/v1`. Breaking schema changes require a new contract version or explicit migration. TypeScript types should be generated from canonical OpenAPI/Pydantic schemas rather than hand-maintained duplicates.
