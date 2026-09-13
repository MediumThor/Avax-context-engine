# UI Directive

## Product goal

The UI must make market context, uncertainty and model performance legible at a glance. It is not a decorative trading dashboard and not a trade-entry terminal.

Technology:
- React
- TypeScript / TSX
- TradingView Lightweight Charts for primary time-series rendering
- responsive web first; native wrappers may follow later

## Primary workspace

The default screen is a single analysis workspace with five synchronized regions:

1. **Market header** — symbol, current price, data freshness, source/exchange, regime summary, and the **recursive agent kill switch**.
2. **Main chart** — candlesticks, volume, structural zones, context overlays, forecast fan.
3. **Context rail** — 1W/1D/4H/1H/15m/5m regime and state transitions.
4. **Forecast panel** — horizons +1..+10, model ensemble, quantiles, calibration and disagreement.
5. **Thesis panel** — active bull/bear hypotheses, evidence, counter-evidence, confirmation and immutable invalidation.
6. **Loop inspector** (replay and accuracy surfaces) — Recursive Learning Harness depth, halt reason, citations, and whether the explanation is incumbent or `harness-degraded`.

## Main chart requirements

Use Lightweight Charts directly; do not recreate a charting engine.

Required layers:
- OHLC candles;
- volume histogram;
- EMA overlays configurable 9/20/50/100/200;
- validated support/resistance **zones** as shaded ranges, not arbitrary thin lines;
- swing pivots;
- breakout/retest/failure markers;
- forecast q10/q50/q90 fan for next 10 5m horizons;
- state-change markers;
- optional Fib overlays generated from exact Context Engine anchors;
- optional analyst annotations visually distinct from system-derived structures.

Every derived overlay needs inspectable provenance. Hover/tap a zone to see why it exists, when it became known and which timeframes support it.

## Forecast visualization

Do not draw one fake future candlestick path as if certain.

Preferred representation:
- median projected path line;
- q10-q90 translucent envelope;
- optional q25-q75 inner envelope;
- horizon dots for probability of positive cumulative return;
- zone-touch probabilities near relevant zones.

When model disagreement is high, visually widen uncertainty or explicitly show disagreement. Never imply precision the evaluator does not support.

## Context rail

Each timeframe row shows:
- regime;
- HH/HL/LH/LL structural state;
- volatility state;
- nearest validated support/resistance;
- last meaningful state-change time.

Clicking a timeframe changes chart granularity but does not erase the higher-timeframe hierarchy.

## Thesis panel

Bull and bear cases appear side by side rather than hiding the non-selected case.

Each shows:
- status;
- evidence;
- counter-evidence;
- exact confirmation;
- exact invalidation;
- age;
- originating context snapshot.

Closed hypotheses remain accessible in history.

## Accuracy panel

Expose model quality honestly:
- direction accuracy by horizon;
- Brier score/calibration;
- q10-q90 empirical coverage;
- MAE by horizon;
- performance by regime;
- baseline comparison;
- sample count.

A green "accuracy" badge without target definition and sample count is prohibited.

Loop depth is not an accuracy badge. Show `depth_used` / `halt_reason` as process metadata, not as "smarter because more loops."

## Recursive agent kill switch

The kill switch is always visible on the primary workspace. It is the operator's hard stop for every Recursive Learning Harness / wave-1 agent.

Engage:

- severs all `active`/`launched` agent tasks;
- blocks new loop runs;
- freezes promotion;
- shows a severed banner;
- leaves candles, journals, and forecasts intact;
- never enables execution.

Reset requires a second confirmation and is append-only. A green "agents healthy" treatment after reset is not an accuracy claim.

## Data-health UX

If data is stale, missing, gapped or model output is old:
- show a prominent state;
- dim/disable forecast claims as appropriate;
- state the last known-good timestamp;
- never silently continue as if live.

## Mobile

Mobile is a first-class read/analysis experience.

- chart occupies most of viewport;
- bottom sheet contains context/forecast/thesis tabs;
- horizontal swipe may change timeframe only if it cannot conflict with chart pan;
- tap targets >= 44px;
- data-health and regime always visible;
- no hover-only information.

## Visual hierarchy

Use restrained financial-tool styling. Information density is acceptable, ambiguity is not.

Prioritize:
1. current regime and freshness;
2. price/structure;
3. forecast uncertainty;
4. invalidations;
5. performance evidence;
6. secondary indicators.

## UI agent completion criteria

A UI change is complete only when:
- responsive behavior is tested at mobile/tablet/desktop sizes;
- keyboard access works for controls;
- chart resize does not leak listeners;
- all displayed metrics come from typed contracts;
- no invented placeholder statistics appear in production mode;
- visual regression snapshots are updated intentionally;
- loading/error/stale states are implemented.
