# Context Engine Directive

## Mission

The Context Engine is the persistent market-state layer. Its job is to understand where current price action sits inside larger structures so the system does not overreact to isolated candles.

It must be deterministic wherever practical and inspectable at every transition.

## Required timeframe hierarchy

- 1W
- 1D
- 4H
- 1H
- 15m
- 5m

Each timeframe maintains independent state while also referencing parent/child state.

## Required state per timeframe

At minimum:

- trend regime: bullish / bearish / neutral / transition;
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
  "timeframes": ["1D", "4H"],
  "sources": ["swing_cluster", "volume_reaction"],
  "strength": 0.0,
  "tests": 0,
  "last_test_at": "...",
  "status": "active|broken|reclaimed|retired",
  "provenance": []
}
```

Strength is derived from reproducible evidence, not subjective labels.

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

Invalidation rules are immutable for that thesis version. If analysis changes, close the old thesis and create a new one.

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
  "at": "...",
  "entity": "AVAXUSDT:1H",
  "from": "bearish",
  "to": "transition",
  "cause": ["reclaim_zone_7_50_7_55", "higher_low_confirmed"],
  "input_snapshot": "sha256:..."
}
```

This enables replay and postmortem analysis.

## Acceptance criteria

Context Engine v1 is complete when:

- state can be rebuilt from raw candles deterministically;
- no lookahead is present;
- zones and pivots expose `observed_at`/`known_at` semantics;
- hierarchy prevents 5m noise from silently resetting 4H state;
- the September 2026 regression replay produces the expected regime transition around failed resistance and breakdown;
- every state rendered in UI has provenance.
