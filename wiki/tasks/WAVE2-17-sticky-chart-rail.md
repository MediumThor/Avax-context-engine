# WAVE2-17 — Keep the main chart visible while the rail scrolls

```md
Task: Desktop workspace keeps Lightweight Charts on screen. The context rail scrolls independently so thesis/zone cards do not hide the candles.
Agent: 00
Branch: cursor/sticky-chart-rail-8771
Priority: P1
Source main commit: cfa834c

Why:
Constitution §12 and UI-Directive require the main chart and thesis rail on the same workspace. A 720px chart plus a long rail made page-scroll hide the candles. Dogfood screenshots of theses showed a black void where the chart should stay.

Allowed write scope:
- apps/web/src/styles.css
- tests/test_web_workspace.py
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-17-sticky-chart-rail.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Finish criteria:
Desktop viewport shows candles and thesis cards together. Mobile still stacks. No execution controls.
```
