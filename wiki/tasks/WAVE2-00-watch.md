# WAVE2-00 — Watcher audit and RLH core

```md
Task: Publish a live work graph and land EncoderMemory + LoopStep + challenge + SWA + process metrics + five leakage probes on an isolated branch for mainline integration.
Agent: 00
Branch: cursor/watcher-wave2-rlh-core-8771
Priority: P0

Why:
Wave-1 Task agents produced no implementation. RLH is the current critical path. PR 8 owns the honest market UI/API slice; Watcher must not collide with it.

Allowed write scope:
- artifacts/watcher/**
- services/harness/**
- services/evaluator/rlh/**
- tests/harness/**
- tests/rlh/**
- tests/leakage/rlh/**
- wiki/tasks/WAVE2-00-watch.md
- benchmarks/rlh/avax-2026-09-failed-8/notes.md

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- apps/web/src/App.tsx
- services/api/main.py
- packages/models/baselines.py
- packages/context_engine/engine.py

Acceptance tests:
- python -m pytest -q tests/harness tests/rlh tests/leakage/rlh tests/contracts tests/test_kill_switch.py
- no overlap with PR 8 paths

Finish criteria:
Hashed EncoderMemory, deterministic LoopStep, challenge/invalidation, SWA merge, process metrics, five leakage probes, Watcher work graph.
```
