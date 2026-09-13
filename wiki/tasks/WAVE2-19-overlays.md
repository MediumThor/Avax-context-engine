# WAVE2-19 — Context overlays

Watcher owner: Agent 00
Review mode: UI
Competing task group: wave2-web-overlays
Integration dependency: none (isolated component; App wiring is PR 8 / Agent 17)
Target main gate: `npx tsc --noEmit` in `apps/web`

```md
Task: Isolated React overlay that renders provided structural zones as ranges, plus pivot/state-change markers, breakout/retest/failure events, analyst annotations, and non-hover provenance inspection.
Agent: 19
Branch: cursor/wave2-19-overlays-4499
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G6 (UI increment); does not claim G3 context fixtures are accepted

Why:
Constitution §9 and §12 and wiki/UI-Directive.md require validated support/resistance as shaded ranges with inspectable provenance, and require system-derived structure to be visually distinct from analyst annotations. The current MarketChart is candles-only. This task adds a standalone overlay component that a later owner can compose onto the chart without inventing levels or wiring App.tsx in this change.

Inputs:
- CONSTITUTION.md (§4 no fake certainty, §9 real structure, §12 UI reasoning state, §17 no execution)
- wiki/Home.md
- wiki/UI-Directive.md
- wiki/Data-Contracts.md StructuralZone shape (id, lower, upper, role, strength, test_count, known_at, provenance)
- wiki/Context-Engine-Directive.md zone-as-range and breakout semantics
- apps/web/src/api/types.ts StructuralZone (READ ONLY; this task does not own the shared type)
- apps/web/src/components/MarketChart.tsx (READ ONLY; no overlay primitives on main)

Allowed write scope:
- apps/web/src/components/ContextOverlays.tsx
- wiki/tasks/WAVE2-19-overlays.md

Forbidden write scope:
- CONSTITUTION.md
- apps/web/src/App.tsx
- apps/web/src/styles.css
- apps/web/src/components/MarketChart.tsx
- apps/web/src/components/ForecastFan.tsx
- apps/web/package.json
- packages/**
- services/**
- any invented market levels not supplied in props
- real trade / order UI
- fabricated confidence percentages

Dependencies:
- No new npm packages.
- Does not wait for Agent 11 zone fixtures or Agent 18 chart primitive APIs.
- Caller must pass zones/pivots/events/annotations. The component MUST NOT synthesize AVAX (or any) levels.

Implementation requirements:
1. Export named `ContextOverlays`.
2. Props: `zones` as {id, lower, upper, role, strength, test_count, optional known_at/provenance}; optional `pivots`; optional `events` with kinds breakout | retest | failure; optional `analystAnnotations`.
3. Zones render as shaded ranges at the provided lower/upper bounds. Never thicken a degenerate (lower === upper) record into a fake zone line.
4. System vs analyst differ by label and pattern (not color alone): SYSTEM = diagonal hatch + "SYSTEM" badge; ANALYST = dotted stipple + dashed outline + "ANALYST" badge.
5. Provenance is inspectable by tap and keyboard. Hover is never the only path.
6. Missing or empty provenance, missing known_at, and missing timestamps are labeled as unknown. Do not backfill.
7. Strength is shown as the provided field, explicitly not a calibrated confidence.
8. Optional caller `priceMin`/`priceMax` may align the plot later; if omitted, the domain is derived only from provided prices, with layout padding only.
9. Do not mount the component in App.tsx.
10. TypeScript, mobile-first (360px), 44px tap targets for inspectable controls, visible focus.

Acceptance tests:
- command: npx tsc --noEmit
  expected: exit 0 in apps/web
- command: git diff --name-only origin/main
  expected: only the two allowed paths
- manual / review:
  - empty props render an honest empty state and invent no levels
  - a support zone is a band, not a 1px line
  - analyst annotation is labeled ANALYST and uses a different pattern than SYSTEM
  - selecting a zone from the list or plot (keyboard or tap) fills the provenance panel
  - missing provenance copy is explicit
  - no order ticket, submit, or execution control exists

Metrics gate:
- baseline: MarketChart has no structure overlay on main
- required result: isolated component compiles; no accuracy or forecast claims

Historical regressions:
- Do not encode the September 2026 AVAX ~$8 failed-breakout prices as default demo levels in this component.

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-19-overlays.md (this contract)

Completion report must contain:
- files changed
- what the component renders
- tests run and results
- metrics before/after (N/A for accuracy)
- limitations
- whether any contract/schema changed
- recommended next task
- no accuracy claims

Finish criteria:
ContextOverlays.tsx exists with a named export; task contract is on the branch; tsc passes; work is committed and pushed; Watcher (not this agent) opens the PR.
```
