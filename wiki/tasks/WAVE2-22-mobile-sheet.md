# WAVE2-22 — Phone analysis bottom sheet

```md
Task: On viewports ≤900px, keep the 5m chart visible and put Context / Forecast / Thesis / Journal in one segmented bottom sheet. Desktop rail order stays Regime → Thesis → Forecast.
Agent: 00
Branch: cursor/mobile-sheet-8771
Priority: P1

Why:
UI-Directive and Navigation-Directive require a chart-first phone workspace. Stacking every rail card under the chart hid 4h invalidation and forced page scroll.

Allowed write scope:
- apps/web/src/App.tsx
- apps/web/src/styles.css
- tests/test_mobile_sheet.py
- wiki/UI-Directive.md
- wiki/Navigation-Directive.md
- wiki/tasks/WAVE2-22-mobile-sheet.md

Forbidden:
- CONSTITUTION.md
- recursive schemas
- baselines.py
- services/api/runtime.py
- MarketChart.tsx

Acceptance tests:
- python -m pytest -q tests/test_mobile_sheet.py tests/test_web_workspace.py
- npx tsc -b --pretty false (apps/web)

Finish:
- Health and a compact regime strip stay visible with the candles.
- `?panel=` selects the sheet; invalid values fall back to context.
- Desktop still shows every rail card; thesis remains under regime.
- No execution. No fabricated accuracy.
```
