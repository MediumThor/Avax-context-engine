# Internal AI Harness Directive

## Mission

The Internal AI Harness is the reasoning interface between structured market state and the operator. It is custom. It must not become a replacement for the deterministic Context Engine or quantitative evaluator.

The harness is allowed to explain, compare, challenge, summarize, retrieve analogs and propose experiments. It is not allowed to invent data, rewrite historical predictions, or manufacture calibrated probabilities.

## Design principles

1. Tool-first reasoning: the model queries structured tools instead of relying on screenshots or prose memory.
2. Persistent context: the harness receives current and prior state transitions, not merely the newest candle.
3. Competing hypotheses: always make bull and bear evidence available.
4. Evidence provenance: every material claim should be traceable to state, model output or data query.
5. Separation of concerns: deterministic math stays outside the LLM.
6. Measured uncertainty: the harness communicates model calibration and disagreement rather than intuitive confidence percentages.
7. Replayability: given the same snapshot and harness version, analysis should be reproducible enough to audit.

## Required tools

### market.get_snapshot
Returns symbol, timestamp, data freshness and all timeframe regime summaries.

### market.get_series
Returns bounded OHLCV and optional derived features for a specified symbol/timeframe/range.

### context.get_zones
Returns validated support/resistance zones, status, strength and provenance.

### context.get_structure
Returns swing sequence, pivot metadata, breakout/retest events and regime transitions.

### context.get_hypotheses
Returns active competing pattern/thesis hypotheses with evidence, counter-evidence, confirmation and invalidation.

### forecast.get_current
Returns the immutable current forecast for horizons +1..+10, model ensemble components, quantiles and calibration metadata.

### forecast.get_history
Returns prior forecasts and realized outcomes for analogous or recent periods.

### evaluation.get_metrics
Returns global and regime-sliced performance, calibration and baseline comparisons.

### analog.search
Searches historical context-state fingerprints for similar prior conditions without leaking future information into a live forecast.

### system.get_health
Returns source freshness, missing candles, model age, context-engine status and journal write status.

## Harness output contract

Primary analysis should be structured internally as:

```json
{
  "regime": {},
  "what_changed": [],
  "what_did_not_change": [],
  "bull_case": {},
  "bear_case": {},
  "forecast_summary": {},
  "invalidation": {},
  "data_health": {},
  "confidence_source": "calibrated|model-disagreement|insufficient-data"
}
```

The user-facing explanation can be concise, but it must preserve the distinction between measured facts, model forecasts and interpretation.

## No screenshot primacy

Screenshots may be accepted as auxiliary operator input, but they are not canonical market data. If screenshot values conflict with the market data service, the discrepancy must be surfaced. The harness should prefer exact timestamped candles from data tools.

## Counter-thesis requirement

For every directional synthesis, invoke an internal challenge step:

- What evidence would make the opposite direction more likely?
- Has any claimed support/resistance actually been validated?
- Is a lower-timeframe observation being allowed to override a higher-timeframe regime?
- Is a probability being quoted from calibrated model output or intuition?
- Did any invalidation already trigger?

The challenge result is stored with the analysis snapshot.

## Memory model

The harness memory should contain:

- current market-state snapshot ID;
- active hypotheses and their versions;
- recent state transitions;
- model version/performance summary;
- operator annotations separately tagged from system facts;
- prior analysis mistakes promoted into regression rules.

Do not store mutable prose summaries as the sole truth source.

## Harness evaluation

Create a test suite of historical snapshots. For each, evaluate whether the harness:

- identifies the correct higher-timeframe regime from supplied state;
- respects invalidations;
- distinguishes relief bounce from regime reversal;
- cites real zones rather than arbitrary annotations;
- reports calibrated probabilities faithfully;
- does not use future data;
- says "no thesis change" when a new 5m candle is immaterial.

## Recursive / looped operation

The production reasoning architecture is the Recursive Learning Harness. Read and implement:

- [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md)
- [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md)
- [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md)
- [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md)
- [`Recursive-Evaluation.md`](Recursive-Evaluation.md)
- [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md)
- [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md)

Required additions to the tool list:

- `loop.get_state`
- `loop.cite`
- `loop.halt`

More reasoning depth is valuable only when it improves reproducible decision quality, latency/cost tradeoffs and hallucination rates. Infinite depth means an extensible path **across candles**, not unbounded work inside one 5m close. Architecture novelty must not bypass evaluation.

Local models or specialist agents may be swapped into `D_φ` only as versioned `harness_version` challengers.
