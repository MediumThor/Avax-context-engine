# RLH-30 — Loop evaluator

```md
Task: Process-metric runner for RLH fixtures. Invented zones/probabilities/uncalibrated percents fail.
Agent: 30
Branch: cursor/agent-30-rlh-eval-ee66
Model: Grok 4.6
Priority: P0

Why:
Depth is an experiment. Process quality is blocking.

Inputs:
- wiki/Recursive-Evaluation.md
- benchmarks/rlh/*/expected_invariants.json
- packages/contracts/recursive/loop-trace.schema.json

Allowed write scope:
- services/evaluator/rlh/**
- tests/rlh/**

Forbidden write scope:
- CONSTITUTION.md
- benchmarks/rlh/avax-2026-09-failed-8/** (Agent 28)
- benchmarks/rlh/invalidation-already-fired/** (Agent 28)
- weakening process metrics to pass a model

Implementation requirements:
1. score_trace(LoopTrace) -> process metrics: encode_check_present, challenge_present, halt_present, no_uncalibrated_percent, no_invented_probability, parent_regime_not_overwritten.
2. Fail fixtures that invent a zone or quote a confidence percentage without confidence_source enum.
3. Runner command documented: python3 -m tests.rlh or pytest tests/rlh.
4. Do not claim forecast accuracy.

Acceptance tests:
- invented zone fails
- invented probability fails
- uncalibrated percent fails
- well-formed example LoopTrace from packages/contracts/recursive/examples/ can be scored

Finish criteria:
tests/rlh runner green on synthetic pass/fail cases.
```
