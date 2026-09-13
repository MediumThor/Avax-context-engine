# Navigation Directive

## Goal

Navigation must reinforce the system's mental model on a phone: current market state first, evidence second, evaluation third, project operations last. Avoid app sprawl and breakpoint-specific route trees.

## Primary routes

### `/`
Redirect to `/market/AVAXUSDT`.

### `/market/:symbol`
Primary live analysis workspace. Tabs/panels are subordinate to the market view rather than separate disconnected pages.

Subsections:
- Overview
- Structure
- Forecast
- Hypotheses
- Journal
- Accuracy

### `/replay/:snapshotId`
Historical point-in-time replay. The operator can view exactly what the system knew at a forecast timestamp, then reveal subsequent candles separately.

Must also render the journaled `LoopTrace`: depth used, halt reason, citations, challenge result, and encoder-vs-SWA conflicts. Revealing future candles must not re-run `D_φ` against those candles. See [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

### `/benchmarks`
Walk-forward and regression benchmark explorer.

### `/models`
Incumbent/challenger registry, versions, feature schemas, calibration and promotion history.

### `/health`
Data-source health, missing candles, model freshness, journal status, service status.

### `/system`
Context state/event explorer, agent-generated artifacts, build version, upstream dependency pins, kill-switch state.

The prototype shell keeps the **Pause predictions** control on the sticky market header so it is never more than one glance away.

## Navigation rules

1. Market context is never hidden behind more than one interaction from the primary chart.
2. Switching timeframe preserves selected symbol, relevant overlays and hypothesis context.
3. Changing symbol must reload all state from typed API contracts; never reuse stale AVAX context for another asset.
4. Replay mode must be visually unmistakable and must not show future candles until the user explicitly reveals them.
5. Accuracy links must carry the currently selected model and horizon filters when possible.
6. Browser URLs must encode meaningful state so views are shareable/reproducible.

## Mobile-first navigation

The phone implementation defines navigation behavior. Use a compact bottom navigation with no more than five primary destinations:
- Market
- Replay
- Accuracy
- Health
- More

Within Market, use a bottom sheet or segmented control for Structure / Forecast / Thesis / Journal.

Tablet and desktop may render the same destinations as a side rail or top-level workspace navigation, but route names, selected state, deep links, and browser history behavior remain identical.

## Deep-link contract

Preferred query keys:
- `tf=5m|15m|1h|4h|1d|1w`
- `at=<ISO timestamp>` for replay contexts
- `model=<model id>`
- `h=<1..10>`
- `overlay=<comma list>`
- `loop=<loop_trace_id>`
- `depth=<int>` for inspecting a prefix of the journaled loop

Invalid query state must degrade to safe defaults rather than crash.

## Navigation QA

Every route must define:
- loading state;
- no-data state;
- stale-data state;
- API-error state;
- mobile layout;
- browser back/forward behavior.

Test every route at 360px and 390px before accepting tablet or desktop evidence. The Pause predictions status/action must remain reachable without displacing the primary chart or depending on hover.
