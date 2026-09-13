# RLH-28 — Challenge step

```md
Task: Mandatory CHALLENGE + INVALIDATION_CHECK before directional halt. Fill founding fixtures.
Agent: 28
Branch: cursor/agent-28-rlh-challenge-ee66
Model: Grok 4.6
Priority: P0

Why:
Loops otherwise talk past a dead thesis or call a 5m bounce a 4H reversal.

Inputs:
- wiki/AI-Harness-Directive.md
- wiki/Recursive-Learning-Harness.md
- benchmarks/rlh/avax-2026-09-failed-8/*
- packages/contracts/recursive/recurrent-state.schema.json

Allowed write scope:
- services/harness/loop/challenge/**
- tests/harness/challenge/**
- benchmarks/rlh/invalidation-already-fired/**
- benchmarks/rlh/avax-2026-09-failed-8/**

Forbidden write scope:
- CONSTITUTION.md
- services/harness/loop/*.py except what lives under challenge/
- moving fixture invalidation prices after seeing outcomes
- packages/contracts/recursive/**

Implementation requirements:
1. CHALLENGE must run before HALT on any directional synthesis.
2. Attempt to edit an active invalidation → halt reason invalidation_move_attempt.
3. September 2026 fixture: 4H remains bearish through a 5m relief bounce; expected_invariants stay true.
4. Store challenge result on the trace emit.

Acceptance tests:
- missing CHALLENGE fails a process-metric helper
- invalidation edit attempt halted
- avax-2026-09-failed-8 expected_invariants.json still asserts parent bear + no moved invalidation

Finish criteria:
Challenge module + fixture notes. No hindsight-perfect trade call required.
```
