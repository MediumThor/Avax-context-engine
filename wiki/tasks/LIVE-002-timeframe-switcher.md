# Task contract: Chart timeframe switcher

```md
Task: Add a 5m/15m/1H/4H/1D/1W chart switcher. Changing granularity must not rewrite the regime stack or forecast origin.
Agent: 17/18/01 (this cloud agent)
Branch: cursor/live-avax-chart-86f1
Base: LIVE-001 on this branch
Priority: P0
Kill switch: not engaged

Why:
UI Directive: clicking a timeframe changes chart granularity but does not erase the higher-timeframe hierarchy. The workspace only drew 5m bars.

Allowed write scope:
- services/api/runtime.py
- services/api/main.py
- apps/web/src/App.tsx
- apps/web/src/api/market.ts
- apps/web/src/api/types.ts
- apps/web/src/components/TimeframeSwitcher.tsx
- apps/web/src/components/MarketChart.tsx
- apps/web/src/styles.css
- tests/test_timeframe_switcher.py
- wiki/tasks/LIVE-002-timeframe-switcher.md
- wiki/UI-Directive.md
- wiki/Build-Roadmap.md

Forbidden:
- CONSTITUTION.md
- changing 4H/1W regime from 5m chart clicks
- enabling execution
- using unfinished parent bars as closed chart candles
- rewriting quantile scoring

Acceptance:
- Switcher labels: 5m, 15m, 1H, 4H, 1D, 1W
- GET /api/v1/market/{symbol}/candles?timeframe=4h returns closed 4h bars
- Two market payloads with timeframe=5m vs 4h share the same 4h regime
- Fixture path resamples closed 5m only
- Invalid timeframe -> 400
- URL ?tf= updates without wiping as_of
```
