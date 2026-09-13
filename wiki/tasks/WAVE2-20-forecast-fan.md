# WAVE2-20 — Forecast fan visualization

```md
Task: Isolated ForecastFan that renders next-10 5m q10/q50/q90 envelopes, median path, per-horizon probability, and optional caller-supplied disagreement — never a single deterministic future candle path.
Agent: 20
Branch: cursor/wave2-20-forecast-fan-ea2a
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G6 product UI increment (component only; App wiring owned by PR 8)

Watcher owner: Agent 00
Review mode: UI
Competing task group: none
Integration dependency: App.tsx wiring is out of scope (PR 8)
Target main gate: typecheck ForecastFan; Watcher opens the PR

Why:
Constitution §4 and §12 and wiki/UI-Directive.md require the operator to see a probabilistic next-10 5m forecast (median + quantile envelope + disagreement), not one invented future candle path. The Web App shell still has a forecast placeholder.

Inputs:
- CONSTITUTION.md (§4 no fake certainty, §12 UI must expose forecast bands and disagreement, §17 no execution)
- wiki/Home.md
- wiki/UI-Directive.md (Forecast visualization)
- wiki/Data-Contracts.md (ForecastPackage horizons; web field names differ)
- wiki/Documentation-Standards.md (h=1..10 displayed as +1..+10)
- apps/web/src/api/types.ts ForecastHorizon (read-only contract for this task)
- apps/web/src/components/MarketChart.tsx (read-only; do not edit or overlay)

Allowed write scope:
- apps/web/src/components/ForecastFan.tsx
- wiki/tasks/WAVE2-20-forecast-fan.md

Forbidden write scope:
- CONSTITUTION.md
- apps/web/src/App.tsx
- apps/web/src/styles.css
- apps/web/src/components/MarketChart.tsx
- apps/web/package.json
- services/api/**
- packages/**
- real trade execution
- fabricated confidence percentages
- forecast accuracy claims

Dependencies:
- ForecastHorizon already on main in apps/web/src/api/types.ts:
  h, expected_cum_return, p_close_above_origin, q10_cum_return, q50_cum_return, q90_cum_return
- Data-Contracts.md ForecastPackage examples use *_cum_log_return. This component consumes the Web App type field names as-is and does not silently reinterpret them as log returns.
- No new npm dependencies.

Implementation requirements:
1. Named export `ForecastFan`. TypeScript/React. Isolated component only — do not import it from App.tsx in this task.
2. Props accept horizons 1..10 matching `ForecastHorizon`. Optional inner q25/q75 only when the caller supplies both values; never interpolate or invent missing quantiles.
3. Render a translucent q10–q90 envelope and a q50 median path. Do not draw OHLC/future candles as a certain path.
4. Show per-horizon `p_close_above_origin` as the typed model field, labeled as such — not as a subjective confidence percentage and not as accuracy.
5. If disagreement metadata is passed, show the caller label and optionally apply pixel-space visual padding from a caller-supplied widen factor. Do not compute a disagreement score from the quantiles.
6. Empty, error, missing-quantile, and crossed-quantile (q10 <= q50 <= q90 required) states must be labeled. Reject unusable horizons rather than drawing them as valid.
7. Accessible: values visible without hover; color is not the only signal; keyboard-selectable horizons; works at 360px/390px via inline layout (no styles.css edit).
8. Export `inspectForecastHorizons` so later QA can test invariants without this task adding a test file (test paths are outside write scope).

Acceptance tests:
- command: apps/web TypeScript check including ForecastFan.tsx
  expected: no type errors in ForecastFan.tsx
- command: git diff --name-only against source main
  expected: only the two allowed paths
- invariant: inspectForecastHorizons rejects crossed or non-finite quantiles
- invariant: component copy contains no accuracy claim and no invented confidence
- visual: envelope + median + table/picker; no deterministic future candles

Metrics gate:
- baseline: none (visualization only; no forecast-quality claim)
- required result: no accuracy, coverage, or calibration numbers invented in the UI

Historical regressions:
- none owned by this task (September 2026 failed-breakout remains a context/thesis case, not a fan-chart claim)

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-20-forecast-fan.md (this contract)

Completion report must contain:
- files changed
- what the component renders
- tests run and results
- metrics before/after (n/a for accuracy)
- limitations
- no accuracy claims
- next task (Watcher PR + later App.tsx wiring)

Finish criteria:
ForecastFan.tsx exists on this branch, typechecks, stays unwired from App.tsx, and Watcher can open the PR. Temporary branch is isolation only; integration target remains main.
```

## Implementation note (Agent 20)

- Source `main`: `b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7`
- Isolation branch: `cursor/wave2-20-forecast-fan-ea2a`
- Named export: `ForecastFan` plus `inspectForecastHorizons` / `quantileOrderOk`
- Not imported by `App.tsx`
- Kill switch at start: not engaged
- Write-scope check: no other active task owns these two paths

### Tests run

- `npx tsc --noEmit` in `apps/web` — pass
- Runtime invariants on `inspectForecastHorizons` (valid draw, crossed reject, missing quantile reject, empty, gap honesty, h=11 reject, probability-out-of-range labeled but envelope still drawn, `quantileOrderOk`) — pass

### Metrics

Not applicable. No forecast-quality, coverage, or accuracy number is produced or claimed.

