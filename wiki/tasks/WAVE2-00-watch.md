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

## WAVE-2 review board (2026-09-13)

Implementers cannot open PRs. Watcher opened these after scope review. None merged to `main` yet.

| lane | PR | note |
| --- | --- | --- |
| 00 RLH core | [#9](https://github.com/MediumThor/Avax-context-engine/pull/9) | this branch |
| 01 integrity | [#10](https://github.com/MediumThor/Avax-context-engine/pull/10) | reviewed |
| 02 FreqAI boundary | [#11](https://github.com/MediumThor/Avax-context-engine/pull/11) | reviewed |
| 03 features | [#15](https://github.com/MediumThor/Avax-context-engine/pull/15) | CI green after renaming `test_feature_leakage.py` |
| 08 OSS log | [#21](https://github.com/MediumThor/Avax-context-engine/pull/21) | docs only, no deps |
| 10 ATR pivots | [#14](https://github.com/MediumThor/Avax-context-engine/pull/14) | reviewed |
| 11 zones | [#16](https://github.com/MediumThor/Avax-context-engine/pull/16) | reviewed |
| 12 fib | [#18](https://github.com/MediumThor/Avax-context-engine/pull/18) | reviewed |
| 14 cross-market | [#19](https://github.com/MediumThor/Avax-context-engine/pull/19) | reviewed |
| 15 thesis | [#12](https://github.com/MediumThor/Avax-context-engine/pull/12) | reviewed |
| 16 replay | [#17](https://github.com/MediumThor/Avax-context-engine/pull/17) | reviewed |
| 20 ForecastFan | [#20](https://github.com/MediumThor/Avax-context-engine/pull/20) | not wired into App.tsx |
| 35 registry | [#22](https://github.com/MediumThor/Avax-context-engine/pull/22) | draft gates, no scores |
| 37 red team | [#23](https://github.com/MediumThor/Avax-context-engine/pull/23) | tests only |
| 13 patterns | [#24](https://github.com/MediumThor/Avax-context-engine/pull/24) | reviewed |
| 36 leakage | [#25](https://github.com/MediumThor/Avax-context-engine/pull/25) | tests only |
| 19 overlays | [#26](https://github.com/MediumThor/Avax-context-engine/pull/26) | not wired into App.tsx |

PR 8 remains in flight and owns `engine.py` / API / App. Integrate accepted WAVE-2 PRs to `main` only after CI green and no path overlap with PR 8.

## Integration candidate (2026-09-13)

Local merge of reviewed WAVE-2 branches onto `main` `b6bbbf4` produced **220 passed, 1 skipped** (`PYTHONPATH=. python3 -m pytest -q`). PR 8 (honest slice) and PR 13 (prediction-improvement-loop) were excluded. No Constitution edits. No path overlap with PR 8.

## Post-integrate status (2026-09-13 later)

`main` is `811ea80` (WAVE-2 integrate + honest slice PR 8). Watcher next increment: journaled empirical next-10 quantiles on `cursor/empirical-quantiles-8771` (includes WAVE2-05 research emitter). Contract: [`WAVE2-00-empirical-quantiles.md`](WAVE2-00-empirical-quantiles.md).

Do not merge PR 13 without a dedicated review. Do not rewrite `packages/models/baselines.py`. Do not claim FreqAI beats baselines.
