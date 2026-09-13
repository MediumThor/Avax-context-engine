# WAVE2-00 — Show the failed-breakout window and zone events

```md
Task: Widen the default 5m pane so the September ~$8 rejection is on-chart, and mark rejected / accepted-through zone events. Not confidence.
Agent: 00
Branch: cursor/chart-breakout-window-8771
Priority: P1
Source main commit: 6c6bc50

Why:
UI-Directive requires breakout/retest/failure markers. A 240-bar pane starts 2026-09-01 06:00 and hides the Aug 28–29 $8.19 rejection that is the permanent regression case.

Allowed write scope:
- services/api/main.py
- services/api/runtime.py
- apps/web/src/App.tsx
- apps/web/src/components/MarketChart.tsx
- apps/web/src/components/ContextOverlays.tsx
- tests/test_chart_breakout_window.py
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-00-chart-breakout-window.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Finish: Default market payload includes a 5m candle at the $8.19 rejection. Failure/breakout markers use zone last_test_at. Replay still hides later bars. No execution.
```
