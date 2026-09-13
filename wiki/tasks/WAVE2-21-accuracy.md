# WAVE2-21 — Isolated accuracy / calibration panel

```md
Watcher owner: Agent 00
Review mode: UI
Competing task group: wave2-ui-panels
Integration dependency: none (component is isolated; not imported by App.tsx)
Target main gate: npx tsc --noEmit in apps/web
```

```md
Task: Isolated React AccuracyPanel that renders explicit, caller-supplied evaluation metrics by horizon and optional regime. Missing or zero-sample values stay unknown / not yet scored / sample insufficient. No generic accuracy badge. No invented ECE, Brier, coverage, or return-error numbers.
Agent: 21
Branch: cursor/wave2-21-accuracy-6c61
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G6 (display-only; does not require accepted G5 artifacts to compile)

Why:
Constitution §4 and §12 plus wiki/UI-Directive.md require recent forecast quality to be visible as defined metrics (sample count, return error, Brier/calibration, interval coverage, baseline comparison, regime slices). A green undefined "accuracy" badge is prohibited. The Web App shell has no such surface yet. This increment lands the isolated panel so later navigation work can mount it without inventing scores.

Inputs:
- CONSTITUTION.md (§4 no fake certainty, §6 baselines, §12 UI, §17 no execution)
- wiki/Home.md
- wiki/UI-Directive.md (Accuracy panel)
- wiki/Simulation-Accuracy.md (metrics and reporting)
- wiki/Testing-Directive.md (accuracy reporting test: definition, horizon, window, n, baseline)
- wiki/Documentation-Standards.md (horizon +1..+10, no invented stats)
- wiki/ML-FreqAI-Directive.md (distinguish direction, calibration, return error, coverage)
- apps/web existing shell (read-only; not modified)

Allowed write scope:
- apps/web/src/components/AccuracyPanel.tsx
- wiki/tasks/WAVE2-21-accuracy.md

Forbidden write scope:
- CONSTITUTION.md
- apps/web/src/App.tsx
- apps/web/src/styles.css
- apps/web/src/components/MarketChart.tsx
- apps/web/src/components/ForecastFan.tsx
- apps/web/src/components/ContextOverlays.tsx
- apps/web/package.json
- packages/**
- services/**
- fabricating ECE/Brier/coverage numbers
- claiming a model is production-ready
- wiring the panel into the live shell

Dependencies:
- No new npm packages
- No shared schema change (Agent 31 remains contract owner)
- Evaluation Engine manifests are not consumed in this increment; the panel only displays values the caller passes

Implementation requirements:
1. Export a named `AccuracyPanel` from apps/web/src/components/AccuracyPanel.tsx.
2. Props / row type must require explicit metric fields: horizon, n, mae, rmse, brier, ece, coverage, baseline_delta; regime optional.
3. Missing numeric scores render "unknown" or "not yet scored". Never substitute a placeholder percentage.
4. If n is 0 or absent, the slice states that the sample is insufficient and numeric scores for that slice are not shown.
5. Show metric definitions in the accessible document, not hover-only tooltips.
6. Do not import the panel from App.tsx. Do not add demo scores inside the component.
7. Do not claim production-readiness or invent calibration quality.
8. Self-contained styles only (styles.css is out of scope). Mobile-first, keyboard visible, 44px filter targets.

Acceptance tests:
- command: npx tsc --noEmit
  cwd: apps/web
  expected: exit 0; AccuracyPanel.tsx typechecks
- review: no field named `accuracy` without metric definition, horizon, window, sample count, and baseline label
- review: empty / n=0 / null metric paths render insufficient or not-yet-scored copy
- review: App.tsx is unchanged and does not import AccuracyPanel

Metrics gate:
- baseline: no accuracy surface on main (b6bbbf4)
- required result: isolated typed panel; zero invented scores; no production-ready claim

Historical regressions:
- September 2026 AVAX failed-breakout case is not scored by this UI increment
- Do not reinterpret or display hindsight accuracy for that episode

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: generic accuracy badges; hover-only metric definitions

Docs to update:
- wiki/tasks/WAVE2-21-accuracy.md (this contract)

Completion report must contain:
- files changed
- test results
- metrics before/after
- limitations
- next task

Finish criteria:
AccuracyPanel is committed and pushed on cursor/wave2-21-accuracy-6c61; tsc --noEmit passes if the web toolchain is available; CONSTITUTION.md is unchanged; no App.tsx wiring; no fabricated scores.
```
