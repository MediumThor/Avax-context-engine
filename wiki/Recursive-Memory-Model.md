# Recursive Memory Model

The Recursive Learning Harness keeps three memory banks, matching the RLT diagram: **Context KV**, **State**, and **SWA KV**. Mixing them is how loops start inventing structure or leaking the future.

## Bank 1 — EncoderMemory (Context KV)

Name in RLT: encoder KV memory `M^E`, available before decoder replay.

This is the global, prefix-restricted fact memory at `as_of`.

Contents:

- `MarketStateSnapshot` for every required timeframe;
- structural zones with `known_at` / status / provenance;
- active and recently closed hypotheses;
- cross-market BTC/ETH/AVAXBTC slices;
- ForecastPackage IDs and calibration refs (not a second copy of mutable model guts);
- data-health and source hashes;
- prior journal IDs whose `as_of < current as_of`.

Rules:

1. Built by the causal encoder (Context Engine + feature assembler) **before** the first `LoopStep`.
2. Immutable for the life of that `LoopTrace`.
3. Hierarchical: `1W` / `1D` / `4H` / `1H` / `15m` / `5m` are separate slices.
4. A 5m observed token updates only the 5m slice. It cannot rewrite parent regime, parent swing state, or parent invalidations.
5. Rebuildable from raw candles + engine versions. Cache corruption is recoverable.
6. Hash (`encoder_memory_hash`) is stored on the journal row.

The harness may *read* EncoderMemory. It may not *write* it. Context mutations go through the deterministic engine on the next candle, not through a loop argument.

## Bank 2 — Recurrent state `s_t`

Name in RLT: recurrent output / complete state component `s_t`.

This is working synthesis: what the loop currently believes it should say.

Minimum typed fields:

```json
{
  "regime_reading": {},
  "what_changed": [],
  "what_did_not_change": [],
  "bull_case": {},
  "bear_case": {},
  "forecast_summary": {},
  "invalidation": {},
  "data_health": {},
  "confidence_source": "calibrated|model-disagreement|insufficient-data",
  "open_questions": [],
  "citations": []
}
```

Rules:

1. `s_t` is scratch. The journaled `LoopTrace` plus snapshot are the audit truth.
2. Warm-start from the previous candle's halted state is allowed as initialization, never as evidence.
3. If `s_t` asserts a zone, probability, or invalidation missing from EncoderMemory / ForecastPackage, `D_φ` must drop the claim and emit a contradiction event.
4. `confidence_source` is an enum, not a made-up percentage.
5. Parent/child regime language must follow [`Market-State-Spec.md`](Market-State-Spec.md): a 5m bounce inside a 4H bear is not a reversal.

## Bank 3 — Sliding-window KV `C_t^D`

Name in RLT: layerwise decoder SWA cache. A window of `W` includes the current token and at most `W-1` historical entries.

This is the recent loop transcript in structured form.

Default `W = 16` production, `W = 32` research. Each entry stores:

- step index `t`;
- token kind;
- tool name / IO hashes if any;
- citation IDs;
- emit hash;
- whether the step was `exact` or `non_exact`.

Rules:

1. Eviction is FIFO. Evicted steps remain in the durable `LoopTrace`; they just leave the hot window.
2. SWA is for recency, not long-term memory. Long-term facts live in EncoderMemory or the prediction journal.
3. Do not store operator chat or screenshots as SWA keys.
4. Replay must reconstruct the same window contents after each step, not only the final summary.

## Merge

RLT: "Merge uses SWA unless layer uses cached KV."

AVAX merge:

```text
if query is a fact/regime/zone/probability:
    read EncoderMemory (cached KV)
else if query is "what did we just conclude / challenge / retrieve":
    read SWA
else:
    read both; EncoderMemory wins on conflict
```

Conflict events are appended to the trace as `kind=contradiction` metadata on the current step. They do not silently resolve toward the narrative.

## Persistence map

| bank | live store | durable store | rebuild |
| --- | --- | --- | --- |
| EncoderMemory | versioned snapshot | snapshot blob + hash | raw candles + context engine version |
| `s_t` | in-loop object | final + optional prefix snapshots in `LoopTrace` | replay `D_φ` |
| SWA | ring buffer | every step in `LoopTrace.steps[]` | replay `D_φ` |

Derived caches may be discarded. Journaled traces may not.

## What must never be a memory bank

- Unjournaled chat transcripts as sole truth;
- screenshots;
- future candles;
- mutable "accuracy %" badges;
- operator notes mixed into EncoderMemory (operator notes are separately tagged annotations);
- a second hidden thesis that is not in the thesis ledger.

## Cross-candle recurrence

RLT's unbounded temporal depth is the path across tokens. For this project the long path is **across 5m closes**:

```text
... → LoopTrace(T-2) → LoopTrace(T-1) → LoopTrace(T) → ...
```

Each trace is a new decoder prefill over a new encoder memory, optionally warm-started. That is how the system stays living without treating one candle as an infinite inner loop.

Higher-timeframe encoder slices change only when those candles close. The recurrent path may notice a 5m event; it may not promote that event to 4H memory.
