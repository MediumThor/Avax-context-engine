# WAVE2-00 — Leakage-safe swing pivots on the 5m pane

```md
Task: Expose confirmed swing pivots on each timeframe state and draw 5m/4h markers on the LWC pane. Only pivots whose confirmation bar is known.
Agent: 00
Branch: cursor/chart-swing-pivots-8771
Priority: P1
Source main commit: e362d42

Why:
UI-Directive requires swing pivots on the main chart. The engine already computes confirmed_pivots (left/right=3) but drops them. Zones without the source swings are harder to audit.

Allowed write scope:
- packages/context_engine/models.py
- packages/context_engine/engine.py
- apps/web/src/api/types.ts
- apps/web/src/App.tsx
- apps/web/src/components/MarketChart.tsx
- tests/test_swing_pivots_snapshot.py
- wiki/UI-Directive.md
- wiki/Market-State-Spec.md
- wiki/tasks/WAVE2-00-chart-swing-pivots.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. Serialize last confirmed pivots with extreme time, known_at, price, kind.
2. A pivot is unavailable before its confirmation bar.
3. Chart markers use extreme open_time unix so they sit on an existing 5m candle.
4. Not confidence. Not a breakout claim.

Finish: Fixture 5m pane shows confirmed highs/lows. Replay cannot show later-known pivots. No execution.
```
