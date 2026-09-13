# Data Contracts

## Principles

Contracts are versioned, typed and explicit. Services communicate through schemas, not undocumented dictionaries.

Internal timestamps are UTC ISO-8601 or Unix epoch milliseconds. Candle boundaries are aligned to exchange/server time after normalization.

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

No feature pipeline may treat an unfinished candle as closed without an explicit `partial=true` feature namespace.

## MarketStateSnapshot

```json
{
  "id": "snapshot-id",
  "symbol": "AVAXUSDT",
  "as_of": "...",
  "schema_version": "1",
  "data_manifest_id": "...",
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
  "active_hypothesis_ids": []
}
```

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

## Hypothesis

```json
{
  "id": "...",
  "symbol": "AVAXUSDT",
  "direction": "bear",
  "kind": "failed_breakout_continuation",
  "status": "active",
  "created_at": "...",
  "evidence": [],
  "counter_evidence": [],
  "confirmation_rules": [],
  "invalidation_rules": [],
  "closed_at": null,
  "closure_reason": null,
  "version": 1
}
```

An active hypothesis's invalidation rules are immutable. Changed reasoning creates a new hypothesis version.

## ForecastPackage

```json
{
  "id": "...",
  "symbol": "AVAXUSDT",
  "base_timeframe": "5m",
  "forecasted_at": "...",
  "context_snapshot_id": "...",
  "model_ensemble_id": "...",
  "feature_schema_version": "...",
  "data_manifest_id": "...",
  "horizons": [
    {
      "h": 1,
      "expected_cum_log_return": 0.0,
      "p_close_above_origin": 0.5,
      "q10_cum_return": -0.01,
      "q50_cum_return": 0.0,
      "q90_cum_return": 0.01,
      "expected_mfe": 0.0,
      "expected_mae": 0.0,
      "zone_touch_probabilities": {}
    }
  ],
  "component_models": [],
  "calibration_ref": "...",
  "health": "valid"
}
```

## ForecastOutcome

```json
{
  "forecast_id": "...",
  "h": 1,
  "matured_at": "...",
  "realized_cum_return": 0.0,
  "realized_direction": true,
  "realized_mfe": 0.0,
  "realized_mae": 0.0,
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

## StateTransition

```json
{
  "id": "...",
  "symbol": "AVAXUSDT",
  "timeframe": "1h",
  "at": "...",
  "entity": "regime",
  "from": "neutral",
  "to": "bearish",
  "causes": [],
  "input_snapshot_hash": "sha256:..."
}
```

## API versioning

Expose contracts under `/api/v1`. Breaking schema changes require a new contract version or explicit migration. TypeScript types should be generated from canonical OpenAPI/Pydantic schemas rather than hand-maintained duplicates.
