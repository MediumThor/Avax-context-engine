# Agent roster — RLH wave 1

Living assignment board. Agent 00 updates this when a lane is claimed, blocked, integrated, or closed. Do not start work that is `blocked` or owned by another active agent.

**Model for this wave:** Grok 4.6  
**Batch:** `RLH-wave-1`  
**Canonical product branch:** `main`  
**Integration target:** `main`  
**Watcher:** Agent 00  

> Rapid-prototype mode: the run refs below are temporary implementation/isolation sources. Several were launched before the mainline-only policy was adopted. They do not define project state. Agent 00 must reconcile every accepted result onto current `main`, rerun the required tests there, and record the resulting main SHA.

## Active locks

| path | owner | status |
| --- | --- | --- |
| `CONSTITUTION.md` | none (immutable) | locked |
| `packages/contracts/recursive/` | Agent 25 | active |
| `services/harness/schemas/` | Agent 25 | active |
| `services/harness/encoder/` | Agent 26 | active |
| `tests/harness/encoder/` | Agent 26 | active |
| `services/harness/loop/` except `challenge/` | Agent 27 | active |
| `tests/harness/loop/` | Agent 27 | active |
| `services/harness/loop/challenge/` | Agent 28 | active |
| `tests/harness/challenge/` | Agent 28 | active |
| `benchmarks/rlh/avax-2026-09-failed-8/` | Agent 28 | active |
| `benchmarks/rlh/invalidation-already-fired/` | Agent 28 | active |
| `services/harness/memory/` | Agent 29 | active |
| `tests/harness/memory/` | Agent 29 | active |
| `services/evaluator/rlh/` | Agent 30 | active |
| `tests/rlh/` | Agent 30 | active |
| `.github/workflows/` | Agent 33 | active |
| `tests/leakage/rlh/` | Agent 36 | active |
| `artifacts/watcher/` | Agent 00 | active |

## Wave 1 (parallel, Grok 4.6)

| agent | task | temporary source | contract | status | run |
| --- | --- | --- | --- | --- | --- |
| 00 | Watcher artifacts + review authority | `cursor/agent-00-rlh-watch-ee66` | [RLH-00](tasks/RLH-00-watch.md) | launched → integrate to main | [00](bc-9996471d-d66b-544b-897a-746eb95bee07) |
| 25 | Schema stubs / generated types | `cursor/agent-25-rlh-schema-ee66` | [RLH-25](tasks/RLH-25-schema-stubs.md) | launched → integrate to main | [25](bc-ce2386ac-ef67-5abf-89df-0f62bb3ebbeb) |
| 26 | EncoderMemory builder + read tools | `cursor/agent-26-rlh-encoder-ee66` | [RLH-26](tasks/RLH-26-encoder-memory.md) | launched → integrate to main | [26](bc-d8aaf7c2-47b5-5614-8ed4-ebd78c30f0d9) |
| 27 | Same-transition LoopStep | `cursor/agent-27-rlh-loopstep-ee66` | [RLH-27](tasks/RLH-27-loopstep.md) | launched → integrate to main | [27](bc-e46a3bba-daab-50da-98b1-3fcea720ddf7) |
| 28 | Challenge + invalidation step | `cursor/agent-28-rlh-challenge-ee66` | [RLH-28](tasks/RLH-28-challenge.md) | launched → integrate to main | [28](bc-dac4081a-3646-574f-b494-24eebc3f0e53) |
| 29 | SWA window + merge | `cursor/agent-29-rlh-swa-ee66` | [RLH-29](tasks/RLH-29-swa.md) | launched → integrate to main | [29](bc-585b2aff-378b-5f1d-9f8c-84727305a991) |
| 30 | Process metrics + fixture runner | `cursor/agent-30-rlh-eval-ee66` | [RLH-30](tasks/RLH-30-eval.md) | launched → integrate to main | [30](bc-aa834c0d-7f9a-5d91-a09f-7482b09bf974) |
| 33 | CI gate for RLH contracts | `cursor/agent-33-rlh-ci-ee66` | [RLH-33](tasks/RLH-33-ci.md) | launched → integrate to main | [33](bc-77a8126d-c585-5525-ae72-7b4b23eaf83f) |
| 36 | Leakage red team | `cursor/agent-36-rlh-leakage-ee66` | [RLH-36](tasks/RLH-36-leakage.md) | launched → integrate to main | [36](bc-52e0198b-cdf2-5fe2-ac05-32de29f90652) |

## Wave 2

Wave 2 starts from the latest `main` after required Wave 1 dependencies are present there. It does not wait for a separate integration branch.

| agent | task | dependency gate on main |
| --- | --- | --- |
| 16 | Encoder replay from raw candles | Agent 26 builder integrated |
| 06 | Depth walk-forward | Agent 27 loop + forecast engine integrated |
| 07 | Calibration language | forecast packages integrated |
| 21 | Loop UI | journaled traces available |
| 37 | Replay red team | replay path integrated |
| 38 | Dogfood diary | shadow-live path available |
| 39 | Independent replication | ablation artifacts available |

## Rules

1. One writer per path. If you need a locked path, stop and file a Watcher note.
2. Code against accepted JSON schemas on `main`, not against another agent's private implementation.
3. No forecast accuracy claims. No Constitution edits. No real execution.
4. Completion reports include files, tests, metrics (N/A if none), limitations, and the accepted `main` SHA.
5. Watcher may reject, quarantine, or reprompt. Do not weaken fixtures to pass.
6. Accepted work is not complete until it exists and passes verification on `main`.
