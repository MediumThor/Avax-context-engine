# WAVE2-11 — Structural zone lifecycle

```md
Task: Implement zone probe/penetration/acceptance/retest/reclaim/retired lifecycle as ranges with provenance.
Agent: 11
Branch: cursor/wave2-11-zones-d9a4
Priority: P0

Why:
Support/resistance must be ranges, not thin lines. A wick through a level is a probe, not a breakout. Acceptance has to be earned with close count and/or ATR distance so the September 2026 AVAX ~$8 failed-breakout episode cannot be rewritten as a living bullish retest after the fact. Zone bounds are invalidation geometry: they must not move after creation.

Inputs:
- CONSTITUTION.md (§3 no moving goalposts, §5 no leakage, §9 real structure, §18 September regression)
- wiki/Context-Engine-Directive.md (zones as objects; breakout semantics)
- wiki/Market-State-Spec.md (approaching/testing/rejected/penetrated/accepted/retesting/reclaimed/retired)
- wiki/Data-Contracts.md (StructuralZone)
- packages/context_engine/structure.py (read-only cluster_zones)
- packages/context_engine/models.py (Candle, Pivot, StructuralZone)

Allowed write scope:
- packages/context_engine/zones.py
- tests/test_zones.py
- wiki/tasks/WAVE2-11-zones.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- packages/context_engine/structure.py (import cluster_zones only; do not rewrite)
- services/harness/**
- apps/web/**

Dependencies:
- Existing cluster_zones / StructuralZone on main
- No overlap with WAVE2-00 harness paths or PR 8 engine/API/UI files

Implementation requirements:
1. Zones are ranges (lower/upper). Degenerate single-price clusters are padded into a band.
2. Interaction states: approaching, testing, rejected, penetrated, accepted, retesting, reclaimed, retired.
3. Acceptance uses close count and/or ATR distance. Wicks alone are not acceptance.
4. Tests distinguish failed breakout (resistance lost after a close beyond) vs successful reclaim (support accepted through, then accepted back).
5. Bounds are frozen at creation. relocate / with_bounds raises ImmutableZoneBoundsError.
6. Unfinished candles and future-bar perturbations must not change earlier state.
7. Provenance is append-only with known_at at or before the observing candle.

Acceptance tests:
- command: python3 -m pytest tests/test_zones.py -q
  expected: all tests pass
- wick through resistance is probe/rejected, never accepted
- one close beyond is penetrated, not accepted (unless ATR distance fires)
- failed breakout vs successful reclaim both covered
- September-spirit relief bounce does not reclaim ~$8 support or move its bounds

Metrics gate:
- baseline: cluster_zones emits static ranges with no lifecycle
- required result: deterministic lifecycle + tests; no forecast accuracy claim

Historical regressions:
- September 2026 AVAX failed ~$8.15–$8.20 tests and acceptance below ~$8 must not be rewritten by a later relief bounce

Docs to update:
- wiki/tasks/WAVE2-11-zones.md (this contract + completion report)

Finish criteria:
zones.py + test_zones.py + this contract exist on the branch; pytest tests/test_zones.py is green; bounds cannot move; wicks are not acceptance; failed breakout ≠ successful reclaim.
```

Watcher owner: Agent 00
Review mode: strict-schema
Competing task group: none
Integration dependency: none

## Public helpers

| helper | role |
| --- | --- |
| `as_range` | ordered lower/upper; pads thin lines into bands |
| `AcceptanceConfig` | close_count and/or ATR distance; wicks ignored |
| `ZoneSpec` | frozen declared range |
| `ZoneTracker` | chronological ingest/replay |
| `track_zones` | replay convenience |
| `specs_from_pivots` | wraps `cluster_zones` without rewriting it |

Contract `status` mapping: approaching/testing/rejected/penetrated → `active`; accepted/retesting → `broken`; reclaimed → `reclaimed`; retired → `retired`.

## Completion report

- **What changed:** Added `packages/context_engine/zones.py` — a chronological zone tracker that treats support/resistance as frozen ranges with append-only provenance. Interaction states are approaching → testing → rejected | penetrated → accepted → retesting → reclaimed | retired. Acceptance is configurable via close count and/or ATR distance; wicks are probes only. `cluster_zones` is imported for seeding and is not rewritten. Bounds cannot be moved after creation (`ImmutableZoneBoundsError`).
- **Files changed:**
  - `packages/context_engine/zones.py` (new)
  - `tests/test_zones.py` (new)
  - `wiki/tasks/WAVE2-11-zones.md` (this file)
- **Tests run:** `python3 -m pytest tests/test_zones.py tests/test_context_engine.py tests/test_leakage.py -q` → **22 passed**.
- **Metrics before/after:** No forecasting metrics. Before: `cluster_zones` emitted static ranges with no lifecycle. After: wick-through is not acceptance; one close beyond is penetration unless ATR distance fires; failed breakout and successful reclaim are distinct outcomes; September-spirit relief bounce does not reclaim ~$8 support or move its bounds; future-bar perturbation does not change earlier state.
- **Known limitations:** Volume expansion is optional (`volume_multiple`) and not used by default. Tracker is not yet wired into `engine.py` (forbidden this task). Role for mixed clusters still comes from `cluster_zones` at seed time. Retire distance is ATR-multiple based, not calendar time.
- **Documentation updated:** this task contract only. `Data-Contracts.md` / `structure.py` unchanged.
- **Contract/schema changed:** no shared schema owner change. Additive types only (`ZoneSpec`, `TrackedZone`, `AcceptanceConfig`, `ZoneProvenance`). `to_dict()` includes both directive `kind`/`tests` and contract `role`/`test_count`.
- **Recommended next task:** Agent 00 / 16 wire `ZoneTracker` into snapshot replay (without silently overwriting 4H state from 5m). Agent 19 can render these ranges and provenance. Agent 13 can consume `failed_breakout` / `successful_reclaim` outcomes as hypotheses.
