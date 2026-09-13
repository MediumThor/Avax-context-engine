# Agent roster — RLH wave 1

Living assignment board. Agent 00 updates this when a lane is claimed, blocked, or closed. Do not start work that is `blocked` or owned by another active agent.

**Model for this wave:** Grok 4.6  
**Batch:** `RLH-wave-1`  
**Base:** `cursor/recursive-learning-harness-ee66`  
**Watcher:** Agent 00  

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

| agent | task | branch | contract | status |
| --- | --- | --- | --- | --- |
| 00 | Watcher artifacts + review authority | `cursor/agent-00-rlh-watch-ee66` | [RLH-00](tasks/RLH-00-watch.md) | active |
| 25 | Schema stubs / generated types | `cursor/agent-25-rlh-schema-ee66` | [RLH-25](tasks/RLH-25-schema-stubs.md) | active |
| 26 | EncoderMemory builder + read tools | `cursor/agent-26-rlh-encoder-ee66` | [RLH-26](tasks/RLH-26-encoder-memory.md) | active |
| 27 | Same-transition LoopStep | `cursor/agent-27-rlh-loopstep-ee66` | [RLH-27](tasks/RLH-27-loopstep.md) | active |
| 28 | Challenge + invalidation step | `cursor/agent-28-rlh-challenge-ee66` | [RLH-28](tasks/RLH-28-challenge.md) | active |
| 29 | SWA window + merge | `cursor/agent-29-rlh-swa-ee66` | [RLH-29](tasks/RLH-29-swa.md) | active |
| 30 | Process metrics + fixture runner | `cursor/agent-30-rlh-eval-ee66` | [RLH-30](tasks/RLH-30-eval.md) | active |
| 33 | CI gate for RLH contracts | `cursor/agent-33-rlh-ci-ee66` | [RLH-33](tasks/RLH-33-ci.md) | active |
| 36 | Leakage red team | `cursor/agent-36-rlh-leakage-ee66` | [RLH-36](tasks/RLH-36-leakage.md) | active |

## Wave 2 (do not start until wave 1 integrates)

| agent | task | reason gated |
| --- | --- | --- |
| 16 | Encoder replay from raw candles | needs 26 builder |
| 06 | Depth walk-forward | needs 27 + forecast engine |
| 07 | Calibration language | needs forecast packages |
| 21 | Loop UI | needs journaled traces |
| 37 | Replay red team | needs 27 replay |
| 38 | Dogfood diary | needs shadow-live |
| 39 | Independent replication | needs ablation artifacts |

## Rules

1. One writer per path. If you need a locked path, stop and file a Watcher note.
2. Code against accepted JSON schemas, not against another agent's unmerged implementation.
3. No forecast accuracy claims. No Constitution edits. No real execution.
4. Completion reports must include files, tests, metrics (N/A if none), limitations, next task.
5. Watcher may reject, quarantine, or reprompt. Do not weaken fixtures to pass.
