# RLH-25 — Schema stubs

```md
Task: Generate typed stubs from packages/contracts/recursive without forking a second schema.
Agent: 25
Branch: cursor/agent-25-rlh-schema-ee66
Model: Grok 4.6
Priority: P0

Why:
Implementers must import one typed EncoderMemory / LoopStep / HaltDecision, not invent dicts.

Inputs:
- packages/contracts/recursive/*.schema.json
- wiki/Recursive-Learning-Contracts.md
- tests/contracts/test_recursive_schemas.py

Allowed write scope:
- packages/contracts/recursive/**
- packages/contracts/README.md
- services/harness/schemas/**

Forbidden write scope:
- CONSTITUTION.md
- services/harness/encoder/**
- services/harness/loop/**
- services/context/**

Implementation requirements:
1. Keep loop_schema_version 1 unless a Watcher-approved bump is required.
2. Add Python TypedDict or dataclasses generated or clearly derived from the JSON schemas.
3. Document how TS types will be generated; do not hand-write a conflicting TS copy.
4. python3 tests/contracts/test_recursive_schemas.py must still pass.

Acceptance tests:
- command: python3 tests/contracts/test_recursive_schemas.py
  expected: all suites PASS
- services/harness/schemas/ can import EncoderMemory, LoopStep, HaltDecision, LoopTrace

Finish criteria:
One schema owner. No duplicate incompatible types.
```
