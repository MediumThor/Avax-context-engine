# WAVE2-18 — EMA20/50 overlays on the 5m chart

```md
Task: Attach leakage-safe EMA20/EMA50 to chart candles and draw them on Lightweight Charts.
Agent: 00
Branch: cursor/chart-volume-8771
Priority: P1
Source: volume histogram increment

Allowed write scope: runtime chart rows, MarketChart, types, tests/test_chart_volume.py, wiki/UI-Directive.md

Forbidden: CONSTITUTION.md, recursive schemas, baselines.py

Finish: later closes cannot move earlier EMA values. No execution.
```
