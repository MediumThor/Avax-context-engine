# Recursive Learning Contracts

Canonical machine schemas: [`../packages/contracts/recursive/`](../packages/contracts/recursive/).

This page is the human contract. Agent 25 owns schema edits. Other agents code against an accepted version.

`loop_schema_version`: `1`.

## EncoderMemory

Frozen before the first loop step.

```json
{
  "id": "encmem-...",
  "schema_version": "1",
  "symbol": "AVAXUSDT",
  "as_of": "2026-09-13T09:05:00Z",
  "context_snapshot_id": "snapshot-...",
  "forecast_package_id": "forecast-...",
  "data_manifest_id": "manifest-...",
  "feature_schema_version": "1",
  "context_engine_version": "1",
  "timeframe_slices": {
    "1w": { "regime": "bearish", "last_transition_id": "..." },
    "1d": {},
    "4h": {},
    "1h": {},
    "15m": {},
    "5m": {}
  },
  "zone_ids": [],
  "hypothesis_ids": [],
  "cross_market": {},
  "health": "valid|degraded|stale|unknown",
  "content_hash": "sha256:..."
}
```

`content_hash` covers the payload except the hash field itself.

## RecurrentState

Working synthesis `s_t`.

```json
{
  "schema_version": "1",
  "step_index": 0,
  "regime_reading": {},
  "what_changed": [],
  "what_did_not_change": [],
  "bull_case": {
    "regime_relation": "countertrend",
    "supporting_timeframes": ["5m"],
    "conflicting_timeframes": ["4h", "1d"],
    "claims": [],
    "citations": []
  },
  "bear_case": {
    "regime_relation": "aligned",
    "supporting_timeframes": ["4h", "1d"],
    "conflicting_timeframes": ["5m"],
    "claims": [],
    "citations": []
  },
  "forecast_summary": {
    "forecast_package_id": "forecast-...",
    "quoted_fields": []
  },
  "invalidation": { "fired": [], "intact": [] },
  "data_health": {},
  "confidence_source": "calibrated",
  "open_questions": [],
  "citations": [],
  "contradictions": []
}
```

`confidence_source` enum: `calibrated` | `model-disagreement` | `insufficient-data`.

`regime_relation` enum: `aligned` | `countertrend` | `mixed` | `unknown`. A lower-timeframe bearish case inside a bullish higher-timeframe regime remains a tactical countertrend case until explicit reversal confirmation; the symmetric rule applies to bullish cases inside a bearish parent regime.

## LoopStep

One application of `D_φ`.

```json
{
  "t": 1,
  "kind": "RETRIEVE",
  "harness_version": "rlh-0.1.0",
  "input_token_hash": "sha256:...",
  "encoder_memory_hash": "sha256:...",
  "state_in_hash": "sha256:...",
  "state_out_hash": "sha256:...",
  "swa_in_hash": "sha256:...",
  "swa_out_hash": "sha256:...",
  "tool": {
    "name": "context.get_hypotheses",
    "request": {},
    "response_hash": "sha256:...",
    "as_of": "2026-09-13T09:05:00Z",
    "refused": false,
    "refusal_reason": null
  },
  "emit": {},
  "citations": [],
  "exact": true,
  "latency_ms": 0
}
```

`kind` enum: `ENCODE_CHECK` | `RETRIEVE` | `SYNTHESIZE` | `CHALLENGE` | `FORECAST_REFINE` | `INVALIDATION_CHECK` | `ANALOG` | `NO_CHANGE` | `HALT` | `JOURNAL`.

## HaltDecision

```json
{
  "halted": true,
  "reason": "no_change",
  "depth_used": 4,
  "max_depth": 8,
  "window_w": 16,
  "budget_remaining": 4,
  "citations": [],
  "degraded": false
}
```

`reason` enum: `max_depth` | `no_change` | `challenge_complete` | `stale_or_unknown_data` | `contradiction` | `uncalibrated_confidence` | `invalidation_move_attempt` | `latency_budget` | `watcher_abort`.

## LoopTrace

Append-only record written before the next candle is known.

```json
{
  "id": "loop-...",
  "schema_version": "1",
  "symbol": "AVAXUSDT",
  "as_of": "2026-09-13T09:05:00Z",
  "encoder_memory_id": "encmem-...",
  "encoder_memory_hash": "sha256:...",
  "context_snapshot_id": "snapshot-...",
  "forecast_package_id": "forecast-...",
  "harness_version": "rlh-0.1.0",
  "tool_schema_version": "1",
  "commit_sha": "...",
  "warm_start_from_trace_id": null,
  "steps": [],
  "final_state": {},
  "halt": {},
  "content_hash": "sha256:...",
  "journaled_at": "2026-09-13T09:05:01Z"
}
```

Traces are never overwritten. A correction is a new trace with `supersedes` metadata, not an edit.

## ReplayPackage

```json
{
  "as_of": "2026-09-13T09:05:00Z",
  "encoder_memory_id": "encmem-...",
  "forecast_package_id": "forecast-...",
  "loop_trace_id": "loop-...",
  "reveal_future": false,
  "rebuild_policy": "exact|current_policy",
  "expected_trace_hash": "sha256:..."
}
```

`exact` replay must match `expected_trace_hash` or fail. `current_policy` rebuilds under today's `D_φ` and writes a *new* scored artifact, leaving the original hash untouched.

## LoopOutcome (appended later)

```json
{
  "loop_trace_id": "loop-...",
  "forecast_id": "forecast-...",
  "scored_at": "...",
  "horizon_scores": {},
  "depth_prefix_scores": {},
  "challenge_respected_invalidation": true,
  "parent_regime_preserved": true,
  "leakage_probe_passed": true
}
```

Outcomes attach. They do not rewrite `LoopTrace` or `ForecastPackage`.

## Kill switch

See `packages/contracts/recursive/kill-switch.schema.json` and `packages/harness/kill_switch.py`.

| method | path | purpose |
| --- | --- | --- |
| GET | `/api/v1/agents/kill-switch` | current engage state + audit events |
| POST | `/api/v1/agents/kill-switch` | sever all recursive agent work |
| POST | `/api/v1/agents/kill-switch/reset` | logged resume |
| POST | `/api/v1/loops/run` | stub runner; 423 if severed. Live persist journals a LoopTrace after the forecast row. |
| GET | `/api/v1/loops/{id}` | stored LoopTrace plus `forecast_id`; 404 if missing |
| GET | `/api/v1/theses/{id}` | frozen journaled thesis payload plus `invalidation_fingerprint`; 404 if missing |

## API surface (v1)

| method | path | purpose |
| --- | --- | --- |
| GET | `/api/v1/theses/{id}` | implemented: frozen journaled thesis + fingerprint |
| GET | `/api/v1/loops/{id}` | implemented: stored LoopTrace + forecast_id |
| GET | `/api/v1/loops?symbol=&from=&to=` | list traces |
| POST | `/api/v1/loops/replay` | rebuild under `ReplayPackage` |
| GET | `/api/v1/loops/{id}/outcome` | attached scores |
| GET | `/api/v1/loops/health` | last trace time, halt mix, replay mismatch count |

Breaking changes go to `/api/v2` or a migrated schema version.

## Ownership

| contract | owner | reviewers |
| --- | --- | --- |
| EncoderMemory / Loop* schemas | Agent 25 | Agent 00, 31 |
| Halt policy defaults | Agent 27 + 00 | 36, 37 |
| Tool schemas | Agent 25 | 26, 28 |
| UI rendering of traces | Agent 21 | 23, 38 |
