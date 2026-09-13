# WAVE2-18 — Volume histogram on the main chart

```md
Task: Include candle volume in the market payload and draw a Lightweight Charts histogram under the OHLC pane.
Agent: 00
Branch: cursor/chart-volume-8771
Priority: P1
Source main commit: cebfef8

Why:
UI-Directive requires a volume histogram. The chart currently sends OHLC only, so the TradingView pane cannot show participation.

Allowed write scope:
- services/api/runtime.py (chart candle dict only)
- apps/web/src/components/MarketChart.tsx
- apps/web/src/api/types.ts
- tests/test_chart_volume.py
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-18-chart-volume.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Finish criteria:
Fixture candles expose volume. Histogram draws under the candles. No execution.
```
