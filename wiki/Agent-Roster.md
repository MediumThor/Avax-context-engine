# Agent roster — prototype on main

All Recursive Learning Harness work now lands on **`main`** so the team can prototype on one line of code.

Split wave-1 branches (`cursor/agent-00-…` through `cursor/agent-36-…`) are **retired**. Do not write to them. Do not launch a second copy of a lane on another branch.

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

Former isolated branches are closed. Implement the same contracts from `wiki/tasks/` **on main**.

| agent | task | status |
| --- | --- | --- |
| 00 | Watcher + kill switch | on main |
| 25 | Schema stubs | on main (schemas present) |
| 26–30 | Encoder / LoopStep / challenge / SWA / eval | implement on main |
| 33 | CI | on main |
| 36 | Leakage probes | implement on main |
| 17/04/09 | SLICE-001 honest market/forecast/replay | in progress on `cursor/honest-market-slice-ee66` |

SLICE-001 replaces the sine-wave `$7.26` / `DATA LIVE` shell with fixture-or-Binance candles, Context Engine `as_of` snapshots, journaled drift20 baselines, walk-forward MAE with sample counts, and a September 2026 4H-stability replay. Kill switch remains the hard stop.

## Wave 2

Still gated behind a working LoopStep and journaled traces. Still on `main` when started.
