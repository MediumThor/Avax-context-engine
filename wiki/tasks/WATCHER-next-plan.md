# Watcher next-step plan (2026-09-13)

Canonical `main` at write time: `5ffd4ce`. Kill switch: disengaged. Recursive schemas remain Agent 25 locked. Do not rewrite `baselines.py`. Do not merge PR 13 unreviewed. Do not promote the research quantile path (drift20 still wins q50 MAE).

## On now (Composer 2.5 Fast, isolated branches)

| lane | branch | scope |
| --- | --- | --- |
| 06 | `cursor/rlh-06-depth-8771` | Depth ablation of `run_loop` only. Forecast heads unchanged. |
| 30 | `cursor/rlh-30-fixtures-8771` | Fixture manifests + fail-closed runner. No metric weakening. |
| 36 | `cursor/rlh-36-probes-8771` | Strengthen five leakage probes. Tests first. |

## Watcher increment (this branch)

Leakage-safe EMA 9/100/200 on the 5m pane (20/50 already on main).

## After these land

1. Review 06/30/36 diffs; merge only if scopes hold and tests pass.
2. Zones as shaded ranges on the Lightweight Charts pane (not only the overlay plot).
3. Drain remaining shadow-journal 5m origins as `baseline.drift20` only — no extra quantile emits on the request path.
4. Held-out ECE on live/non-fixture data when a real feed exists. No fabricated confidence.
5. FreqAI/challenger work only as research until it beats drift20 OOS.

## Do not

- Turn execution on.
- Claim accuracy from loop depth or in-sample fit.
- Launch a second writer on `packages/contracts/recursive/` or `services/harness/loop/`.
