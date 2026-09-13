# RLH-30 — RLH fixtures first-class

```md
Task: Manifests, notes, and fail-closed runner for required RLH fixtures.
Agent: 30
Branch: cursor/rlh-30-fixtures-8771
Model: Composer 2.5 Fast
Priority: P0

Why:
Most benchmarks/rlh dirs only had expected_invariants.json. Promotion gates need manifests, notes, and a runner that cannot report passed=true on incomplete fixtures.

Inputs:
- wiki/Recursive-Evaluation.md
- benchmarks/rlh/*/expected_invariants.json
- services/evaluator/rlh/runner.py

Allowed write scope:
- benchmarks/rlh/*/manifest.json
- benchmarks/rlh/*/notes.md
- benchmarks/rlh/README.md
- services/evaluator/rlh/runner.py
- tests/rlh/test_process_metrics.py
- wiki/tasks/RLH-30-fixtures.md

Implementation:
1. Every required fixture dir has manifest.json (fixture_id, purpose, as_of, promotion_allowed: false, artifact presence).
2. Every required fixture dir has notes.md.
3. Runner: missing loop_trace.json → status incomplete/invariants_only, passed=false.
4. Tests: required fixtures exist; incomplete fixtures cannot report passed=true.

Finish criteria:
pytest tests/rlh green; no weakened process metrics; September 2026 notes keep 4H bear / no relief-as-reversal.
```