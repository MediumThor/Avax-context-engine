# Context Engine Directive

## Mission

The Context Engine is the persistent market-state layer. Its job is to understand where current price action sits inside larger structures so the system does not overreact to isolated candles.

It must be deterministic wherever practical and inspectable at every transition.

The Recursive Learning Harness may read Context Engine snapshots as frozen `EncoderMemory`. It may not write context state. A 5m loop argument is not a 4H regime change. See [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md).

## Required timeframe hierarchy

- 1w
- 1d
- 4h
- 1h
- 15m
- 5m

Each timeframe maintains independent state while also referencing parent/child state.

## Required state per timeframe

At minimum:

- trend regime: bullish / bearish / neutral / transition_up / transition_down / unknown;
- swing sequence: HH/HL/LH/LL;
- volatility regime: compressed / normal / expanded;
- EMA geometry and slope state;
- RSI/momentum state;
- validated support/resistance zones;
- recent breakout/retest/failure events;
- volume expansion/contraction state;
- structural invalidation markers;
- active pattern hypotheses;
- timestamp of last meaningful state change.

## Structural zones

Support/resistance zones are objects, not lines.

Each zone must store:

```json
{
  "id": "zone-id",
  "lower": 7.15,
  "upper": 7.35,
  "kind": "support",
  "timeframes": ["1d", "4h"],
  "sources": ["swing_cluster", "volume_reaction"],
  "strength": 0.0,
  "tests": 0,
  "last_test_at": "...",
  "status": "active|broken|reclaimed|retired",
  "provenance": []
}
```

Strength is derived from reproducible evidence, not subjective labels.

Current: `ContextEngine.build_snapshot` walks `ZoneTracker` on each timeframe's closed bars. Specs are seeded from confirmed pivots with role taken at formation `known_at`, not rewritten from the snapshot-time close. A 5m bar cannot ingest a 4h zone. Bounds stay frozen. Interaction/status/outcome are attached on `StructuralZone`. Strength and test_count are not calibrated confidence.

## Swing structure

Implement at least two pivot methods and benchmark them:

1. confirmed local extrema with volatility-adaptive window;
2. zig-zag / ATR threshold pivots.

No pivot can use future information at the forecast timestamp except after enough future candles have occurred to confirm it; a pivot's `known_at` timestamp must be tracked separately from its candle timestamp.

## Breakout semantics

A breakout is not a wick through a line.

Represent:

- probe;
- close beyond zone;
- acceptance beyond zone;
- retest;
- successful reclaim;
- failed breakout;
- failed breakdown.

Acceptance must be configurable using close count, ATR-adjusted distance, volume, or time spent beyond the zone.

## Thesis ledger

Maintain simultaneous competing theses rather than one narrative.

Example:

```json
{
  "id": "bear-continuation-20260913",
  "direction": "bear",
  "regime_relation": "aligned",
  "status": "active",
  "evidence": [],
  "counter_evidence": [],
  "confirmation": [],
  "invalidation": [],
  "created_at": "...",
  "closed_at": null,
  "closure_reason": null
}
```

Invalidation rules are immutable for that thesis version. If analysis changes, close the old thesis and create a new one. Each thesis also records whether it is aligned, countertrend, mixed, or unknown relative to its parent-timeframe regime.

`ContextEngine.build_snapshot` rebuilds a leakage-safe ledger from closed bars known at `as_of` and attaches compact `theses` summaries. A 5m observation cannot fire a 4h invalidation. Competing bull and bear versions may stay active until their own frozen rules fire.

Live snapshots (`persist_theses=True`, kill switch off) then insert those summaries into the journal `theses` table. The same id is insert-only: a later rebuild cannot change `invalidation_fingerprint`. Replay and kill-switch paths bind stored rules when present and mark `ledger` `journaled` or `ephemeral`. They do not insert. `GET /api/v1/theses/{id}` returns the frozen row.

## Pattern hypotheses

Pattern modules may emit hypotheses for:

- trend continuation;
- bear/bull flags;
- wedges/triangles/compression;
- failed breakouts;
- accumulation/distribution;
- Wyckoff-inspired phases;
- Elliott impulse/correction candidates;
- Fibonacci retracement/extension confluence.

Every pattern is a hypothesis with evidence and invalidation, never an unquestioned label.

## Elliott Wave handling

Elliott counts are inherently ambiguous. The engine may maintain multiple candidate counts ranked by rule compliance and fit. Never force a count because five visible peaks exist.

Track:

- pivot sequence;
- overlap rules;
- relative wave lengths;
- Fibonacci relationships;
- alternate counts;
- invalidation levels.

## Fibonacci handling

Fib anchors must come from confirmed structural swings and record exact anchor timestamps/prices. Do not approximate from screenshot geometry. Candidate levels are context features, not guaranteed support.

## Cross-market context

BTC is mandatory contextual input. ETH and AVAXBTC are strongly recommended.

Store:

- rolling beta/correlation;
- relative-strength returns;
- BTC regime;
- BTC volatility expansion;
- synchronized breakdown/breakout flags;
- decoupling events.

## State transition log

Every meaningful change emits an append-only event:

```json
{
  "observed_at": "...",
  "known_at": "...",
  "entity": "AVAXUSDT:1h",
  "from": "bearish",
  "to": "transition",
  "cause": ["reclaim_zone_7_50_7_55", "higher_low_confirmed"],
  "input_snapshot": "sha256:..."
}
```

This enables replay and postmortem analysis.

## Incremental context build order

At each eligible closed `5m` candle, process context in a deterministic order:

1. Validate source completeness and timestamp alignment.
2. Close and persist any newly completed parent-timeframe candles.
3. Confirm newly knowable pivots using `known_at`.
4. Update structural-zone interactions and lifecycle events.
5. Update cross-market state on timestamp-aligned observations.
6. Evaluate timeframe state from parent to child with hysteresis.
7. Append hypothesis/thesis versions and immutable invalidations.
8. Build the versioned context fingerprint and allocate the linked snapshot/fingerprint IDs.
9. Append transitions and durably persist the `MarketStateSnapshot` plus fingerprint as one accepted state update.

The engine may optimize this pipeline, but deterministic replay must preserve the same accepted outputs and ordering semantics.

## Analog retrieval

`ContextEngine.build_snapshot` attaches leakage-safe analog matches on `MarketSnapshot.analogs`.

Rules:

- a candidate origin is eligible only when its h=10 close is already known at snapshot `as_of`;
- the fingerprint uses only the prefix visible at that origin (recent log-returns and realized vol);
- the realized h=10 log-return is attached only because that close is `<= T`;
- analog distance is fingerprint proximity, not a calibrated confidence percentage and not a forecast.

Empty analog lists are valid when history is too short. The UI must label these as historical matches known at T.

## Context fingerprint

A context fingerprint is a versioned, machine-readable projection of the snapshot used for historical analog search and forecasting. It includes regime, structure, zone distance/state, volatility, cross-market alignment, and active-hypothesis features with their availability timestamps.

The fingerprint must reference its source snapshot and schema version. It may not include mutable prose, future outcomes, or values that were not known at the snapshot's `as_of` time.

Live snapshots also carry compact `pattern_hypotheses` (`score_provenance=evidence_count_v1`) and candidate `fib_levels` derived from confirmed pivots known at T. Those fields are hypotheses/features, not privileged structure.

## Acceptance criteria

Context Engine v1 is complete when:

- state can be rebuilt from raw candles deterministically;
- no lookahead is present;
- zones and pivots expose `observed_at`/`known_at` semantics;
- hierarchy prevents 5m noise from silently resetting 4h state;
- the September 2026 regression replay produces the expected regime transition around failed resistance and breakdown;
- every state rendered in UI has provenance.
