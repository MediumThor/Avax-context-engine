# Recursive Learning Harness — agent batch

Launch these contracts after this foundation merges. Agent 00 watches the batch. Do not start two writers on `packages/contracts/recursive/` in the same wave.

Copy a block into a Cursor task. Change only the branch slug if needed. Cloud agents that must use `cursor/<slug>-<id>` keep the same write scope.

## Batch graph

```text
00 Watcher (this protocol)
        │
        ├─ 25 schema lock (if further schema work) ──┐
        │                                            │
        ├─ 26 memory banks ──────────────────────────┤
        ├─ 27 LoopStep / D_φ ────────────────────────┼─▶ 30 eval suite
        ├─ 28 challenge step ────────────────────────┤
        ├─ 29 SWA + summarizer ──────────────────────┘
        │
        ├─ 16 encoder replay (context)
        ├─ 06 depth walk-forward (quant)
        ├─ 07 calibration-by-depth (quant)
        ├─ 21 loop UI
        ├─ 33 CI hooks
        ├─ 36 leakage red team
        ├─ 37 replay red team
        └─ 38 dogfood / 39 independent replication
```

## Agent 00 — Recursive watcher

```md
Task: Stand up recursive watcher artifacts and review the 25-30 wave.
Agent: 00
Branch: agent/00-rlh-watch
Allowed write scope:
- artifacts/watcher/**
- wiki/Recursive-Watcher-Protocol.md (corrections only)
Forbidden: CONSTITUTION.md; packages/contracts/recursive/ except reject notes
Acceptance tests:
- recursive-health.json schema documented
- every 25-30 completion reviewed with the RLH reprompt template
Finish criteria: no overlapping writers; first fixture canary defined
```

## Agent 25 — Tool + loop schema steward

```md
Task: Keep loop/tool schemas valid and generate TS/Pydantic stubs from packages/contracts/recursive.
Agent: 25
Branch: agent/25-rlh-schema-stubs
Allowed write scope:
- packages/contracts/recursive/**
- packages/contracts/README.md
- services/harness/schemas/** (when that tree exists)
Forbidden: CONSTITUTION.md; services/context implementation
Acceptance tests:
- python3 tests/contracts/test_recursive_schemas.py
- generated types compile or are documented as next-step if codegen is not yet wired
Docs: wiki/Recursive-Learning-Contracts.md
Finish criteria: one schema owner; no hand-copied duplicate types
```

## Agent 26 — Encoder memory + retrieval

```md
Task: Implement EncoderMemory builder and harness tools that only read frozen memory at as_of.
Agent: 26
Branch: agent/26-rlh-encoder-memory
Allowed write scope:
- services/harness/**
- services/context/read-models/** (read adapters only)
- tests/harness/**
Forbidden: CONSTITUTION.md; mutating Context Engine writes; packages/contracts/recursive/
Dependencies: accepted EncoderMemory schema
Acceptance tests:
- future-candle perturbation does not change encoder_memory_hash
- unfinished parent candle ignored
- 5m slice cannot write 4H slice
Docs: wiki/Recursive-Memory-Model.md
Finish criteria: builder + get_* tools return hashed memory
```

## Agent 27 — Same-transition LoopStep

```md
Task: Implement D_φ so ingest tokens and emit tokens share one LoopStep, with halt budget.
Agent: 27
Branch: agent/27-rlh-loopstep
Allowed write scope:
- services/harness/loop/**
- tests/harness/loop/**
Forbidden: CONSTITUTION.md; Forecast Engine numeric heads; UI
Dependencies: Agent 26 memory reader
Acceptance tests:
- required step order for directional synthesis
- NO_CHANGE shortcut on immaterial 5m fixture
- live vs exact replay hash match on fixture replay-parity
- max_depth halt fires
Docs: wiki/Recursive-Loop-Spec.md
Finish criteria: one function, versioned harness_version, journal writer stub
```

## Agent 28 — Challenge / counter-thesis step

```md
Task: Make CHALLENGE + INVALIDATION_CHECK mandatory before directional halt.
Agent: 28
Branch: agent/28-rlh-challenge
Allowed write scope:
- services/harness/loop/challenge/**
- tests/harness/challenge/**
- benchmarks/rlh/invalidation-already-fired/**
- benchmarks/rlh/avax-2026-09-failed-8/** (fixtures only)
Forbidden: CONSTITUTION.md; moving fixture invalidation prices after seeing outcomes
Acceptance tests:
- missing CHALLENGE fails process metrics
- September 2026 relief bounce does not reset 4H bear reading
- attempt to edit invalidation emits halt reason invalidation_move_attempt
Docs: wiki/AI-Harness-Directive.md, wiki/Recursive-Learning-Harness.md
Finish criteria: challenge result stored on the trace
```

## Agent 29 — SWA window and state summarizer

```md
Task: Implement W-sized SWA ring and a summarizer that never becomes sole truth.
Agent: 29
Branch: agent/29-rlh-swa
Allowed write scope:
- services/harness/memory/**
- tests/harness/memory/**
Forbidden: CONSTITUTION.md; deleting evicted steps from LoopTrace
Acceptance tests:
- window length never exceeds W
- evicted steps remain in LoopTrace.steps
- merge prefers EncoderMemory on fact conflict
Finish criteria: replay reconstructs identical SWA hashes per step
```

## Agent 30 — Loop evaluation and hallucination tests

```md
Task: Implement Recursive-Evaluation process metrics and fixture runner.
Agent: 30
Branch: agent/30-rlh-eval
Allowed write scope:
- services/evaluator/rlh/**
- tests/rlh/**
- benchmarks/rlh/**
Forbidden: CONSTITUTION.md; weakening process metrics to pass a model
Acceptance tests:
- all required fixtures listed in Recursive-Evaluation.md exist or are stubbed with TODO manifests
- invented zone / invented probability cases fail
- uncalibrated percent fails
Docs: wiki/Recursive-Evaluation.md
Finish criteria: `python -m pytest tests/rlh` or documented runner command is green on stubs + schema
```

## Supporting lanes (second wave)

### Agent 16 — Encoder replay

Rebuild `EncoderMemory` from raw candles. Deterministic snapshot sequence. Write scope: `services/context/replay/**`.

### Agent 06 — Depth walk-forward

Run Forecast Engine unchanged; vary only `max_depth` / halt policy. Publish depth-ablation artifacts. No target renaming.

### Agent 07 — Calibration language

Ensure loop `forecast_summary.quoted_fields` match ensemble calibration refs. No new confidence percentages.

### Agent 21 — Loop UI

Route `/replay/:snapshotId` shows loop depth, halt, citations, SWA vs encoder conflict. No invented metrics. See Navigation + UI directives.

### Agent 33 — CI

Gate PRs that touch `services/harness` or `packages/contracts/recursive` on schema tests + leakage probe smoke.

### Agent 36 — Leakage red team

Own the five probes in Recursive-Evaluation.md. Write scope: `tests/leakage/rlh/**`.

### Agent 37 — Replay red team

Break exact vs current-policy replay. Write scope: `tests/replay/rlh/**`.

### Agent 38 — Dogfood

Daily loop-trace diary. Tag `HARNESS` defects. Promote repeats into fixtures.

### Agent 39 — Independent replication

Re-score a frozen ablation from commit SHA + manifests only.

## Concurrency locks

| path | lock |
| --- | --- |
| `CONSTITUTION.md` | none (immutable) |
| `packages/contracts/recursive/` | Agent 25 only per batch |
| `benchmarks/rlh/avax-2026-09-failed-8/` | Agent 28 or 00 |
| `services/harness/loop/` | Agent 27 then 28 sequentially, not parallel writers |
| `wiki/Recursive-*.md` | one docs agent at a time after this foundation |

## First-week finish gate

The wave is integrated when:

- schema tests pass;
- at least `no-change-5m`, `stale-data`, and `replay-parity` fixtures run;
- September 2026 fixture has expected invariants committed (even if engine is still stubbed);
- Watcher health artifact exists;
- no agent claimed forecast accuracy from loop depth.
