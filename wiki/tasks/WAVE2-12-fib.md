# WAVE2-12 — Fibonacci / measured-move features

```md
Task: Build exact structural Fibonacci retracement/extension features from confirmed swing anchors with timestamp provenance.
Agent: 12
Branch: cursor/wave2-12-fibonacci-a4e0
Model: Grok 4.6
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: none
Integration dependency: existing Pivot contract on main (models.Pivot / structure.py)

Why:
Context Engine Directive requires Fibonacci anchors from confirmed structural swings with exact timestamps and prices. Screenshot geometry is forbidden. Candidate levels are context features, not guaranteed support. A pivot that is not yet confirmed at T must not appear as an anchor at T (Constitution §5 / §9).

Inputs:
- CONSTITUTION.md (immutable; §5 no leakage, §9 real structure, §10 competing hypotheses)
- wiki/Context-Engine-Directive.md (Fibonacci handling; known_at vs candle time)
- wiki/Testing-Directive.md (pivot known_at + leakage)
- packages/context_engine/models.py Pivot contract (read-only)
- packages/context_engine/structure.py (import Pivot type only; do not edit)

Allowed write scope:
- packages/context_engine/fibonacci.py
- tests/test_fibonacci.py
- wiki/tasks/WAVE2-12-fib.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- packages/context_engine/structure.py
- services/harness/**
- apps/web/**

Dependencies:
- Existing Pivot(index, known_at_index, time, known_at, price, kind)
- Confirmed swings supplied by callers (window or ATR methods). This module does not invent pivots.

Implementation requirements:
1. Anchors must be confirmed Pivot instances with known_at. Pixel/price tuples are rejected.
2. Candidate levels are context features (status=candidate). Never promote a ratio to support/resistance.
3. A pivot with known_at > T cannot be used as an anchor at T.
4. No Elliott forced labeling (no impulse/wave-count fields).
5. Retracement: end + (start - end) * ratio. Extension: start + (end - start) * ratio. Measured move: C + (B - A) * ratio.
6. Level known_at is max(anchor known_at values). Prices are exact float arithmetic from pivot.price.

Acceptance tests:
- command: python3 -m pytest tests/test_fibonacci.py -q
  expected: all tests pass
- pivot unknown at T is absent from anchors/levels at T
- mutating a not-yet-known pivot does not change features at T
- 0.618 / 1.618 prices match exact arithmetic
- serialized output has no Elliott labels
- levels remain status=candidate / is_guaranteed_support=false

Metrics gate:
- none (context features, not a forecast model)

Historical regressions:
- none in this increment (September 2026 replay stays with engine/zone/thesis owners)

Docs to update:
- wiki/tasks/WAVE2-12-fib.md (this contract)

Finish criteria:
Tests green. Module consumes Pivot only. Leakage test proves known_at semantics. Branch pushed for Watcher review.
```

## Public helpers

| helper | role |
| --- | --- |
| `pivots_known_as_of` | filter `known_at <= as_of` |
| `swing_anchors` | opposite-kind confirmed A→B swings |
| `measured_move_anchors` | A→B plus C pullback inside the range |
| `retracement_price` / `extension_price` / `measured_move_price` | exact arithmetic |
| `fibonacci_features` | candidate retracement, extension, and measured-move levels |

Consecutive same-kind pivots collapse to the more extreme confirmed swing (lower low / higher high). Zero-range swings are skipped.

Default ratios:

- retracement: 0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0
- extension: 1.272, 1.618, 2.0, 2.618
- measured move: 1.0, 1.272, 1.618 (1.0 is AB=CD)

## Leakage contract

- `time` is when the extreme printed. `known_at` is when confirmation printed.
- Features at T may use a pivot only if `known_at <= T`.
- An A→B anchor is knowable only at `max(A.known_at, B.known_at)`.
- A measured-move setup is knowable only at `max(A.known_at, B.known_at, C.known_at)`.
- Mutating pivots with `known_at > T` must not change `fibonacci_features(..., as_of=T)`.

## Non-goals

- Does not detect pivots (window / ATR methods remain the producers).
- Does not wire levels into `ContextEngine` (`engine.py` is forbidden).
- Does not add UI overlays or forecast numbers.
- Does not assign Elliott wave counts.
- Does not treat a Fibonacci price as structural support.

## Completion report

- **What changed:** Added `packages/context_engine/fibonacci.py` — leakage-safe retracement, extension, and measured-move candidate features built only from confirmed `Pivot` anchors. Levels carry timestamp provenance and are explicitly not support/resistance.
- **Files changed:**
  - `packages/context_engine/fibonacci.py` (new)
  - `tests/test_fibonacci.py` (new)
  - `wiki/tasks/WAVE2-12-fib.md` (this file)
- **Tests run:** `python3 -m pytest tests/test_fibonacci.py tests/test_context_engine.py tests/test_leakage.py -q` → **19 passed** (`test_fibonacci.py` 15 passed).
- **Metrics before/after:** not a forecast model; no accuracy claims. Feature count 0 → exact candidate levels from confirmed swings.
- **Known limitations:** not wired into `ContextEngine`; callers must supply confirmed pivots; confluence scoring vs zones is a follow-up.
- **Documentation updated:** this task contract only. Shared schemas unchanged.
- **Contract/schema changed:** no. Additive feature types only (`SwingAnchor`, `MeasuredMoveAnchor`, `FibLevel`, `FibFeatureSet`).
- **Recommended next task:** Agent 00 / 16 attach `fibonacci_features(pivots, as_of=T)` to timeframe snapshots without promoting levels to zones. Agent 13 can treat confluence as a competing hypothesis.
