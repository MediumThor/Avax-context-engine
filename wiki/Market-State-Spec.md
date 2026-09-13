# Market State Specification

## State hierarchy

Every symbol has one canonical `MarketStateSnapshot` assembled from timeframe states plus cross-market context.

### Timeframe state machine

Allowed regime states:
- `bullish`
- `bearish`
- `neutral`
- `transition_up`
- `transition_down`
- `unknown`

Regime changes should be event-driven and hysteretic. Avoid flipping state on one candle unless a deliberately defined structural event requires it.

## Inputs

Each timeframe state may use:
- completed OHLCV candles;
- confirmed pivots with `known_at` timestamps;
- EMA geometry;
- ATR/realized volatility;
- RSI/momentum;
- validated structural zones;
- breakout/retest state;
- volume state;
- parent-timeframe regime;
- cross-market context.

## Structural score

A regime classifier should expose component scores rather than one opaque label. Example:

```json
{
  "trend_score": -0.8,
  "structure_score": -0.6,
  "momentum_score": -0.2,
  "volume_score": -0.1,
  "parent_alignment": -0.7,
  "final_state": "bearish"
}
```

Exact weighting may be rule-based initially and later learned, but must be versioned and benchmarked.

## Parent/child semantics

Parent state constrains interpretation but does not ban countertrend moves.

Example:
- 4H bearish
- 1H bearish
- 15m transition_up
- 5m bullish

This means a lower-timeframe relief rally inside a bearish higher-timeframe regime, not a global bullish reversal.

The harness should explain this distinction explicitly. The Recursive Learning Harness must preserve this parent/child split in `EncoderMemory` and in `s_t`; see [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

## Meaningful state-change events

Examples:
- confirmed higher low;
- confirmed lower high;
- break/acceptance beyond structural zone;
- reclaim after breakdown;
- failed breakout;
- volatility regime transition;
- parent-regime change;
- relative-strength decoupling.

Indicator crossovers alone should not necessarily be treated as regime changes.

## Zone interaction state

For every active zone, track:
- approaching;
- testing;
- rejected;
- penetrated;
- accepted through;
- retesting from opposite side;
- reclaimed;
- retired.

These event sequences become features and hypotheses.

## State persistence

Snapshots are immutable. The live state pointer advances to a new snapshot after each relevant event/candle. Rebuilding the same historical stream with the same engine version must reproduce the same snapshot sequence.

## September 2026 expected behavior

The founding regression should show that repeated failure around the ~$8.15-$8.20 region can remain a bullish-pressure hypothesis only while the underlying structure continues to support it. Once support around ~$8 fails with lower highs/EMA deterioration and acceptance below, the higher-timeframe state should transition bearish and remain so through small relief bounces until explicit reclaim criteria are met.

The exact prices are benchmark data, not hard-coded universal rules.

## Unknown state

If data integrity is insufficient, return `unknown`. Do not infer continuity across missing candles without explicit gap-handling rules.
