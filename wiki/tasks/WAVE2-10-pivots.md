# WAVE2-10 — ATR/zigzag confirmed pivots (second method)

```md
Task: Add a leakage-safe ATR/zigzag confirmed-pivot method with candle time and known_at, as a second method beside window pivots.
Agent: 10
Branch: cursor/wave2-10-atr-pivots-c433
Model: Grok 4.6
Priority: P1

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: pivot-methods
Integration dependency: none (does not replace packages/context_engine/structure.py)

Why:
Context Engine Directive requires two pivot methods. Window extrema already live in structure.confirmed_pivots. The second method must confirm swings only after an ATR-scaled reversal, and must never expose a pivot before it was knowable.

Inputs:
- CONSTITUTION.md (immutable)
- wiki/Context-Engine-Directive.md (swing structure, known_at)
- wiki/Testing-Directive.md (pivot confirmation + leakage)
- packages/context_engine/structure.py (read-only; do not replace confirmed_pivots)
- packages/context_engine/models.py Pivot contract (read-only)
- packages/context_engine/indicators.py atr() (read-only, causal Wilder ATR)

Allowed write scope:
- packages/context_engine/pivots_atr.py
- tests/test_pivots_atr.py
- wiki/tasks/WAVE2-10-pivots.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/structure.py
- packages/context_engine/engine.py
- services/harness/**
- apps/web/**

Dependencies:
- Existing Pivot(index, known_at_index, time, known_at, price, kind)
- Causal ATR from indicators.atr (data through bar i only)

Implementation requirements:
1. Emit the same Pivot contract as window pivots. time/index is the extreme candle; known_at/known_at_index is the first closed candle that confirms it.
2. A pivot is unavailable before known_at. atr_zigzag_pivots(..., as_of=T) and pivots_known_as_of(...) must exclude known_at > T.
3. Confirmation uses only closed candles at or before the confirmation bar. ATR at bar i uses highs/lows/closes[0..i].
4. Do not replace, wrap, or change confirmed_pivots.
5. No UI. No forecast claims. No execution.

Acceptance tests:
- command: python -m pytest -q tests/test_pivots_atr.py
  expected: all tests pass
- future candles after T must not create pivots with known_at <= T that were not knowable from the prefix through T
- prefix pivots == full-series pivots filtered to known_at <= last prefix time
- as_of=T ignores candles after T
- unclosed candles cannot confirm
- confirmed_pivots remains importable and independently correct

Metrics gate:
- none (structure method, not a forecast model)

Historical regressions:
- none in this increment (September 2026 replay stays with engine/regime owners)

Docs to update:
- wiki/tasks/WAVE2-10-pivots.md (this contract)

Finish criteria:
Tests green. Module is a second method only. Leakage tests prove known_at semantics. Branch pushed for Watcher review.
```

## Algorithm

Causal zigzag over closed candles:

1. Warm up Wilder ATR (`atr_period`, default 14). Skip bars with no ATR.
2. While no pivot is confirmed, track the running high and running low.
3. The first extreme that reverses by `atr_multiple * ATR` (default 2.0) becomes the first confirmed pivot. `known_at` is that reversal bar.
4. After a confirmed high, track a candidate low (and vice versa). Confirm when price retraces `atr_multiple * ATR` from the candidate extreme.
5. Threshold of 0 (flat ATR) never confirms. Extremes update only on a strictly higher high or lower low.
6. Unconfirmed candidates are never returned.

## Leakage contract

- `time` is when the extreme printed. `known_at` is when confirmation printed. Features/snapshots at forecast time T may use a pivot only if `known_at <= T`.
- Processing is prefix-closed: state at bar i depends only on closed candles `0..i`.
- `atr_zigzag_pivots(full, as_of=T)` must equal `atr_zigzag_pivots(prefix through T)`.
- Mutating candles after T must not add, drop, or rewrite any pivot with `known_at <= T`.

## Non-goals

- Does not change window `confirmed_pivots`.
- Does not wire this method into `ContextEngine` (engine.py is forbidden).
- Does not add UI overlays or forecast numbers.
- Sensitivity benchmark vs window pivots is a follow-up (needs a shared eval owner).
