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

### `/replay/:symbol`
Historical point-in-time replay for a symbol (`/replay/AVAXUSDT?as_of=`). The operator can view exactly what the system knew at a forecast timestamp. A `/market/:symbol?as_of=` deep link canonicalizes to this dest. Tapping Replay without `as_of` uses `replay_hint_as_of` from the last market payload (fixture pre-bounce). Tapping Market clears replay.

Must also render the journaled `LoopTrace`: depth used, halt reason, citations, challenge result, and encoder-vs-SWA conflicts. Revealing future candles must not re-run `D_φ` against those candles. See [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

### `/accuracy`
Primary walk-forward AccuracyPanel. Scores come from the market metrics payload. Missing Brier/ECE stay "not yet scored". This dest does not invent a generic accuracy percentage.

### `/benchmarks`
Walk-forward and regression benchmark explorer. Secondary dest (not a sixth bottom-nav item). Reads `GET /api/v1/benchmarks` from the registry. Draft entries stay unsealed. No invented ECE/MAE.

### `/models`
Incumbent/challenger registry. Secondary dest from More. Reads `GET /api/v1/models`. Incumbent is `baseline.drift20`. Research quantile/probability rows stay `promotion_allowed: false`.

### `/health`
`GET /health` plus `GET /api/v1/system`: data-source health, kill-switch, last close, service status. No fabricated ECE/accuracy.

### `/more` (also `/system`)
Project operations: execution stays off, harness/kill-switch summary, journal remaining if already loaded, constitution reminders. `/system` canonicalizes to `/more`.

The prototype shell keeps the **Pause predictions** control on the sticky market header so it is never more than one glance away.

## Navigation rules

1. Market context is never hidden behind more than one interaction from the primary chart.
2. Switching timeframe preserves selected symbol, relevant overlays and hypothesis context. Chart `?tf=` is `5m|15m|1h|4h|1d|1w`; invalid values fall back to `5m`. `apps/web/src/nav/destinations.test.ts` covers dest parse/href including secondary `/benchmarks` and `/models`. CI web runs `npm run web:test`.
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

The prototype shell implements those five dests with `history.pushState` / `popstate` (no react-router). `/` and unknown dests canonicalize to `/market/AVAXUSDT`. Tap targets are ≥44px.

Within Market, use a bottom sheet or segmented control for Structure / Forecast / Thesis / Journal.

Tablet and desktop render the same destinations as a left rail. Route names, selected state, deep links, and browser history behavior remain identical.

## Deep-link contract

Preferred query keys:
- `tf=5m|15m|1h|4h|1d|1w` — Market/Replay honor this. Invalid values degrade to `5m`. The pane uses leakage-safe resampled closed bars from the 5m store; HTF zones stay. Forecast remains the next 10 five-minute candles.
- `at=<ISO timestamp>` for replay contexts
- `as_of=<ISO timestamp>` for fixture/replay market slice
- `panel=<context|forecast|thesis|journal>` — phone analysis sheet; desktop ignores the chrome and still shows the full rail
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
