# WATCH-00 — Merge remaining unique branches onto main

```md
Watcher owner: Agent 00
Review mode: normal
Competing task group: none
Integration dependency: none
Target main gate: PYTHONPATH=. python3 -m pytest -q

Task: Reconcile every remote branch that still has unique commits onto one mainline candidate.
Agent: 00
Branch: cursor/merge-all-branches-a127
Priority: P0
Source main commit: c9a56c27682ec408e001a5a6ed92ab15f5df74ee
Dependency gate: G0

Why:
The operator asked to merge all branches to main. Most remotes are already ancestors of main. Four refs still have unique commits; one of those is an obsolete kill-switch prototype already superseded on main.

Inputs:
- latest origin/main
- origin/cursor/engine-theses-8771 (PR 37)
- origin/cursor/live-avax-chart-86f1 (PR 35)
- origin/cursor/prediction-improvement-loop-ee66 (PR 13)
- origin/cursor/rlh-main-prototype-ee66 (PR 7, obsolete)

Allowed write scope:
- apps/web/**
- packages/context_engine/**
- packages/market_data/binance.py
- packages/contracts/improvement/**
- services/api/**
- tests/**
- wiki/**
- artifacts/watcher/**
- .cursor/plans/**
- .cursor/rules/prediction-improvement.mdc
- .env.example
- .gitignore
- README.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Dependencies:
- current main SHA c9a56c2
- kill switch disengaged

Implementation requirements:
1. Fast-forward from latest main.
2. Merge unique, still-valid work from PRs 37, 35, and 13.
3. Do not replay PR 7; its kill-switch prototype is already on main and would regress App.tsx.
4. Resolve App.tsx / runtime / docs conflicts without weakening journal, leakage, or no-execution rules.
5. Run pytest and record the result.

Acceptance tests:
- command: PYTHONPATH=. python3 -m pytest -q
  expected: all tests pass
- command: git diff -- CONSTITUTION.md
  expected: empty

Metrics gate:
- none (integration, not a model promotion)

Historical regressions:
- September 2026 failed-breakout 4H stability must remain.

Docs to update:
- wiki/tasks/WATCH-00-merge-all-branches.md
- wiki/Agent-Roster.md
- artifacts/watcher/active-tasks.json

Finish criteria:
One PR onto main contains every remaining unique, non-obsolete branch. Obsolete remotes are recorded as already integrated.
```

## Completion (2026-09-13)

- Candidate SHA: `c02ada7090c51dd9e0568a2e8d493ea5fec2ac30` on `cursor/merge-all-branches-a127`
- PR: https://github.com/MediumThor/Avax-context-engine/pull/38
- `bash scripts/check_constitution.sh` — Constitution integrity OK
- `python3 tests/contracts/test_recursive_schemas.py` — passed
- `PYTHONPATH=. python3 -m pytest -q` — **283 passed, 2 skipped**
- `npm run web:build` — passed
- Fixture smoke: `/health` fixture, `/market` returns 2 theses with 4h invalidation frozen at open, `/candles?timeframe=4h` returns closed bars, `execution_enabled=false`
- Browser: FIXTURE header, timeframe switcher, competing theses, replay pre-bounce, kill switch disengaged
- PR 7 not merged (obsolete kill-switch prototype already on `main`)

