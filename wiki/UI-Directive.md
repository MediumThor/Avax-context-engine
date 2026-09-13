# UI Directive

## Product goal

The UI must make market context, uncertainty, and model performance legible first on a phone. It is not a decorative trading dashboard or a trade-entry terminal.

Technology:

- React
- TypeScript / TSX
- TradingView Lightweight Charts for primary time-series rendering
- mobile-first responsive Web App; native wrappers may follow later

Mobile-first means phone information hierarchy, touch interaction, loading cost, and component composition are the base design constraints. Desktop is a progressive enhancement of the same routes and contracts, not a separate implementation.

## Primary workspace

The default screen is a single analysis workspace with six synchronized information regions:

1. **Market header** — symbol, current price, data freshness, source/exchange, regime summary, and the **Pause predictions** control (kill-switch API).
2. **Main chart** — candlesticks, volume, structural zones, context overlays, forecast fan.
3. **Context rail** — 1W/1D/4H/1H/15m/5m regime and state transitions.
4. **Forecast panel** — horizons `h=1..10` (displayed as +1..+10), model ensemble, quantiles, calibration, and disagreement.
5. **Thesis panel** — active bull/bear hypotheses, evidence, counter-evidence, confirmation and immutable invalidation. Journaled rows show `ledger journaled`; that is storage provenance, not confidence.
6. **Loop inspector** (replay and accuracy surfaces) — Recursive Learning Harness depth, halt reason, citations, and whether the explanation is incumbent or `harness-degraded`.

On phones, these regions are not rendered as five simultaneous columns. The market header and chart remain visible; Context, Forecast, Thesis, and Journal use a touch-friendly segmented bottom sheet. Selection state is shared so opening a panel never creates a second, stale copy of market context.

On desktop (`min-width: 900px`) the workspace is viewport-locked: Lightweight Charts stays in the left pane while the context rail scrolls. Thesis and zone cards must not push the candles off-screen.

## Main chart requirements

Use Lightweight Charts directly; do not recreate a charting engine.

Required layers:

- OHLC candles;
- volume histogram (drawn under the candles when `volume` is present on the market payload);
- EMA overlays configurable 9/20/50/100/200 (live 5m pane draws all five from closed closes known at each bar; later candles cannot move earlier values);
- validated support/resistance **zones** as shaded ranges, not arbitrary thin lines (5m pane fills from `known_at` through the last closed candle and autoscales so HTF bounds such as the 4h $8 cap stay in view);
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

When model disagreement is high, visually widen uncertainty or explicitly show disagreement. Never imply precision the Evaluation Engine does not support.

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
- regime relation: aligned / countertrend / mixed / unknown;
- evidence;
- counter-evidence;
- exact confirmation;
- exact invalidation;
- age;
- originating context snapshot.

Closed hypotheses remain accessible in history.

Countertrend hypotheses must be explicitly labeled; color alone is insufficient.

## Accuracy panel

Expose model quality honestly:

- direction accuracy by horizon;
- Brier score/calibration;
- q10-q90 empirical coverage;
- mean absolute error by horizon;
- performance by regime;
- baseline comparison;
- sample count.

A green "accuracy" badge without target definition and sample count is prohibited.

Loop depth is not an accuracy badge. Show `depth_used` / `halt_reason` as process metadata, not as "smarter because more loops."

Current rail card (`LoopTraceCard`): halt reason, analog retrieve count, and hypothesis ids from the live loop summary. Analog count is not confidence.

## Recursive agent kill switch

The kill-switch state and action are always accessible from the compact sticky market header as **Pause predictions** / **Resume predictions**. On phones, confirmation uses a focused sheet/dialog rather than a permanently expanded card that displaces the chart. It is the operator's fail-closed control for new live forecast journal writes, RLH loop execution, and promotion.

The prototype marks registered tasks severed, blocks loop API calls, and skips new forecast journal writes; agents stop cooperatively when they observe the state. Do not tell the operator that an unconnected external process was forcibly terminated.

Pause / engage:

- pauses new live forecast journal writes;
- severs all `active`/`launched` agent tasks;
- blocks new loop runs;
- freezes promotion;
- shows a paused banner;
- leaves candles, journals, and forecasts intact;
- never enables execution.

Resume / reset requires a second confirmation and is append-only. A green "agents healthy" treatment after reset is not an accuracy claim.

## Data-health UX

If data is stale, missing, gapped or model output is old:

- show a prominent state;
- dim/disable forecast claims as appropriate;
- state the last known-good timestamp;
- never silently continue as if live.

If `forecast.shadow_journal.remaining` is greater than zero, the health line and Journal tab show that gap. The count is coverage of mature-able 5m origins, not Brier/ECE/accuracy. Missing `shadow_journal` stays unknown.

## Mobile

Phone layout is the reference implementation.

- Start design and tests at 360px and 390px CSS viewport widths before tablet/desktop expansion.
- Keep symbol, price, data health, and higher-timeframe regime in a compact sticky header.
- Give the chart the primary viewport area without forcing the operator to dismiss navigation chrome.
- Put Context, Forecast, Thesis, and Journal in one stateful bottom sheet with a stable segmented control. The prototype uses `?panel=` for that selection. Invalid values fall back to Context. A compact regime strip stays above the candles so 4h state is visible when another tab is open. The zone overlay plot is desktop-only; phone operators read zones from the Context tab.
- Preserve the selected symbol, timeframe, forecast horizon, replay timestamp, and overlays when the sheet opens or routes change.
- Do not bind horizontal timeframe swipes where they conflict with chart pan; explicit timeframe controls are always available.
- Use tap targets at least 44 by 44 CSS pixels with adequate separation.
- Keep the Pause predictions action at least 44 by 44 CSS pixels and visually distinct without dominating normal market analysis.
- Provide touch equivalents for every hover inspection and keyboard access for every interactive control.
- Avoid nested horizontal scrolling outside the chart.
- Render stale, degraded, replay, and no-data states without hiding the last-known-good timestamp.
- Load secondary analytics on demand; the live chart and health state must not wait for off-screen panels.

### Tablet and desktop enhancement

- At wider widths, promote bottom-sheet sections into synchronized rails/panels.
- Do not change data semantics, route meaning, or control labels between breakpoints.
- A desktop-only dense view may expose more simultaneous evidence, but every critical action and explanation remains available on mobile.
- Never use desktop screenshots as the sole acceptance evidence for a feature.

### Touch and chart behavior

- One-finger drag pans the chart; pinch zooms when supported by the chart library.
- Vertical page scrolling must remain possible when a gesture begins outside the active chart plot.
- Crosshair inspection must have an explicit touch mode and a clear exit behavior.
- Opening a zone, pivot, or forecast detail must not cause the chart to jump or reset its visible range.
- Resize, route change, and unmount must remove chart listeners and observers.

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

- behavior is first verified at 360px and 390px, then at representative tablet and desktop sizes;
- keyboard access works for controls;
- touch access works without hover dependencies or chart/scroll gesture traps;
- chart resize does not leak listeners;
- all displayed metrics come from typed contracts;
- no invented placeholder statistics appear in production mode;
- visual regression snapshots are updated intentionally;
- loading/error/stale states are implemented.
