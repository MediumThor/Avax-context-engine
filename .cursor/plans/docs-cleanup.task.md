# Documentation Cleanup Task Contract

Task: Make the `main` documentation coherent, mobile-first, recursive-learning-ready, and executable by coordinated agents without changing project law
Agent: 31
Branch: `agent/31-docs-cleanup`
Source `main`: `32339ae`
Integration target: `main`
Priority: P0
Status: complete; pending mainline integration

## Why

The initial documentation establishes strong product intent, but it needs a clearer entry point, an explicit current-state boundary, consistent terminology, dependency-safe agent waves, mobile-first product requirements, durable recursive-learning context, and removal of contradictions that could cause implementation agents to build against different assumptions.

## Inputs

- `CONSTITUTION.md`
- `AGENTS.md`
- `.cursor/rules/*.mdc`
- `.github/pull_request_template.md`
- `README.md`
- `wiki/*.md`

## Allowed write scope

- `README.md`
- `AGENTS.md`
- `.cursor/rules/*.mdc`
- `.github/pull_request_template.md`
- `wiki/*.md`
- `.cursor/plans/docs-cleanup.task.md`

## Forbidden write scope

- `CONSTITUTION.md`
- future application code, tests, schemas, data, and benchmark fixtures

## Assumptions

- The repository contains a prototype implementation spine; each document distinguishes code verified on `main` from target behavior.
- Timeframe values use lowercase canonical API/schema codes and uppercase display labels.
- Agent numbers describe ownership lanes; actual simultaneous concurrency is limited by the active runtime.
- `main` is the only durable integrated product branch; direct work requires an exclusive path lock and runner-required isolation is disposable.
- Phone interaction and information architecture are the Web App baseline; larger layouts are progressive enhancements.

## Implementation requirements

1. Create a useful README and wiki landing page.
2. State current repository maturity without implying unimplemented systems exist.
3. Normalize terminology, timeframe notation, and forecast-horizon language.
4. Resolve cross-document ordering or ownership contradictions.
5. Preserve all Constitution constraints and the founding regression case.
6. Keep agent prompts actionable and retain their bounded write scopes.
7. Define exact dependency gates and ownership boundaries that let agents build the whole system into `main`.
8. Define the evidence, memory, experiment, and promotion loop for recursive AVAX learning.
9. Make mobile acceptance criteria concrete and testable.

## Acceptance tests

- All relative Markdown links resolve to tracked files or documented future artifacts.
- No edit to `CONSTITUTION.md`.
- Documentation uses the canonical terminology rules defined in the wiki.
- `git diff --check` passes.
- A clean reader can identify project purpose, current status, architecture, next build phase, and agent startup path from `README.md` and `wiki/Home.md`.
- Agents can identify what may run in parallel, what must merge first, and who owns shared schemas.
- Recursive changes originate from evidence-linked records and cannot bypass Watcher/main gates.
- UI work begins with 360px/390px touch validation.

## Metrics gate

- Broken relative links: 0
- Constitution changes: 0
- Unexplained current/planned ambiguity in the landing pages: 0

## Historical regressions

- Preserve the September 2026 AVAX failed-breakout regression requirement.

## Docs to update

- `README.md`
- `wiki/Home.md`
- Other documentation files only where consistency or clarity requires it.
- `wiki/Agent-Build-Plan.md`
- `wiki/Documentation-Standards.md`
- `wiki/Continuous-Improvement-Directive.md`

## Finish criteria

Documentation reads as one system specification, contains no material internal contradictions found in review, passes structural checks, and is ready for Watcher review.

## Completion evidence

- Documentation structural/link/anchor/JSON-fence checks: pass (48 Markdown/rule files; 30 top-level wiki pages indexed).
- Constitution integrity check: pass; no Constitution diff.
- Recursive schema/fixture contract suite: pass.
- Python test suite: 18 passed.
- Web App production build: pass.
- Contract/schema changes: documentation-only target contracts; no production schema files changed.
- Known implementation gaps: recorded in [`wiki/Agent-Build-Plan.md`](../../wiki/Agent-Build-Plan.md); documentation does not claim those gates are complete.
