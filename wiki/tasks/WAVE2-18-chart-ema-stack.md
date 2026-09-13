# WAVE2-18 — EMA 9/20/50/100/200 on the 5m chart

```md
Task: Attach leakage-safe EMA9/20/50/100/200 to chart candles and draw them on Lightweight Charts.
Agent: 00
Branch: cursor/chart-ema-stack-8771
Priority: P1

Why:
UI-Directive requires configurable 9/20/50/100/200. The pane only drew 20/50.

Allowed write scope:
- services/api/runtime.py (_chart_rows only)
- apps/web/src/api/types.ts
- apps/web/src/components/MarketChart.tsx
- tests/test_chart_volume.py
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-18-chart-ema-stack.md

Forbidden: CONSTITUTION.md, recursive schemas, baselines.py, harness loop

Finish: later closes cannot move earlier EMA values for any period. No execution.
```
