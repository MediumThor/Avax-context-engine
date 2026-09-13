# WAVE2-00 — Surface shadow-journal remaining on the workspace

```md
Task: Show forecast.shadow_journal wrote/remaining/model_id on the primary workspace so the journal gap is visible. Do not invent accuracy. Do not emit forecasts.
Agent: 00
Branch: cursor/journal-remaining-ui-8771
Priority: P1
Source main commit: c48a3a5

Why:
Constitution §7 and §12 require a journaled forecast at each eligible close and a UI that exposes data health. Request-path catch-up already returns remaining; the web types and Journal panel ignore it.

Allowed write scope:
- apps/web/src/api/types.ts
- apps/web/src/api/market.ts
- apps/web/src/App.tsx
- apps/web/src/components/ShadowJournalCard.tsx
- apps/web/src/styles.css
- wiki/Prediction-Journal.md
- wiki/UI-Directive.md
- wiki/tasks/WAVE2-00-journal-remaining-ui.md

Depends on:
- PR 54 (`POST /api/v1/journal/catchup`) now on main `762e7b2`

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py
- services/api/**

Implementation requirements:
1. Type shadow_journal as wrote/remaining/model_id. Missing payload stays unknown, not zero-invented scores.
2. Journal panel and a compact health-line gap count read the typed field only.
3. Copy must say catch-up is baseline.drift20 only and is not a promotion.
4. Replay and kill-switch states must not imply a write occurred.

Finish criteria:
Operator can see remaining mature-able 5m origins without opening the API. No execution. No fabricated ECE.
```
