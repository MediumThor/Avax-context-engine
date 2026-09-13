# WAVE2-19 — Shaded zones on the 5m Lightweight Charts pane

```md
Task: Draw Context Engine zones as shaded ranges on the candle pane, not only the separate overlay plot.
Agent: 00
Branch: cursor/chart-zones-8771
Priority: P1

Allowed write scope:
- apps/web/src/components/ChartZoneBands.ts
- apps/web/src/components/MarketChart.tsx
- apps/web/src/App.tsx
- tests/test_chart_zones.py
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-19-chart-zones.md

Forbidden: CONSTITUTION.md, recursive schemas, baselines.py, harness loop

Finish: bands use frozen lower/upper; width stops at the last known candle. No execution.
```
