# Agent roster — prototype on main

All accepted Recursive Learning Harness work lands on **`main`** so the team prototypes against one durable product state.

The `temporary_source` refs in `artifacts/watcher/active-tasks.json` are launch provenance for already-running jobs, not product branches. Review each returned candidate against current `main`, integrate accepted work immediately, verify it on `main`, and retire the temporary ref. Do not launch a second copy of a live lane.

**Model:** Grok 4.6 for agent reasoning  
**Batch:** `RLH-wave-1` (integrated)  
**Base:** `main`  
**Watcher:** Agent 00  
**Kill switch:** UI header + `POST /api/v1/agents/kill-switch`  

## Kill switch

Engaging the switch:

- marks every `active` / `launched` task `severed`;
- freezes promotion (`recursive-health.json`);
- blocks `POST /api/v1/loops/run` with HTTP 423;
- marks the harness `degraded`;
- does **not** delete prediction journals, forecasts, or the Constitution;
- does **not** enable trading.

Reset is a second explicit, reason-logged action. Events are append-only.

Prototype enforcement is cooperative for external agents: the repository state marks tasks severed and loop API calls fail closed, but an external runner must observe the state to stop. No direct external-runtime termination adapter is implemented yet.

## Locks during prototype

One writer at a time on a path, even on `main`. If the kill switch is engaged, stop implementing agent features until reset.

| path | owner while unlocked |
| --- | --- |
| `CONSTITUTION.md` | none (immutable) |
| `packages/contracts/recursive/` | Agent 25 |
| `packages/harness/kill_switch.py` | Agent 00 / 31 |
| `apps/web/src/components/AgentKillSwitch.tsx` | Agent 17 / 21 |
| `services/harness/**` | sequential 26 → 27 → 28 → 29 |
| `artifacts/watcher/` | Agent 00 |

## Wave 1 status

The registry is the authority for live status. `launched` means a temporary implementation source may still return; it does not mean its work has passed review or landed on `main`. New or retried work follows the mainline protocol in [`Agent-Build-Plan.md`](Agent-Build-Plan.md).

| agent | task | status |
| --- | --- | --- |
| 00 | Watcher + kill switch + RLH core | on `main` (`0876e71` WAVE-2 integrate) |
| 25 | Schema stubs | on `main` |
| 26–30 | Encoder / LoopStep / challenge / SWA / eval | on `main` |
| 33 | CI | on `main` |
| 36 | Leakage probes | on `main` |
| 17/04/09 | SLICE-001 honest market/forecast/replay | this PR (`cursor/honest-market-slice-ee66`) |

SLICE-001 replaces the sine-wave `$7.26` / `DATA LIVE` shell with fixture-or-Binance candles, Context Engine `as_of` snapshots, journaled drift20 baselines, walk-forward MAE with sample counts, and a September 2026 4H-stability replay. Kill switch remains the hard stop. WAVE-2 modules (features, zones, replay, harness) are already on `main` and are not rewritten here.

## Wave 2

Still gated behind a working LoopStep and journaled traces. Still on `main` when started.
