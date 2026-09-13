# Watcher next-step plan (2026-09-13)

Canonical `main` at write time: `762e7b2`. Kill switch: disengaged. Recursive schemas remain Agent 25 locked. Do not rewrite `baselines.py`. Do not merge PR 13 unreviewed. Do not promote the research quantile path (drift20 still wins q50 MAE). Do not overlap PR 55 (`apps/web` journal-remaining UI).

## On now

| lane | branch | scope |
| --- | --- | --- |
| 07 | `cursor/heldout-live-ece-5716` | Held-out ECE on live/non-fixture journal and walk-forward scores. Fixture ECE stays null. |
| 00/UI | `cursor/journal-remaining-ui-8771` (PR 55) | Shadow-journal remaining count on the workspace. Do not touch those files here. |

## Already landed after previous plan (`5ffd4ce` → `762e7b2`)

1. RLH-06/30/36 (depth ablation, fixture runner, leakage probes).
2. Zone bands on the 5m pane.
3. Journal drain of missing 5m origins as `baseline.drift20` only.

## After this ECE increment lands

1. Review PR 55; merge only if it stays on the journal-remaining UI scope.
2. Close or rebase stale PRs 7 / 13 / 35 / 38. Do not merge #38 while it conflicts.
3. FreqAI/challenger work only as research until it beats drift20 OOS.
4. Retire leftover open prototype PRs that are already on `main`.

## Do not

- Turn execution on.
- Claim accuracy from loop depth, fixture ECE, or in-sample fit.
- Launch a second writer on `packages/contracts/recursive/` or `services/harness/loop/`.
- Touch PR 55 paths (`App.tsx`, `api/market.ts`, `api/types.ts`, `ShadowJournalCard.tsx`).
