# Task contract: Recursive Learning Harness foundation

```md
Task: Publish the Recursive Learning Harness (RLH) wiki, contracts, schemas, watcher protocol, and first implementable agent batch so up to 40 subagents can continuously implement, test, replay, and improve looped reasoning without inventing architecture.
Agent: 25 (schema owner for this batch; Watcher 00 reviews)
Base: latest main
Integration target: main
Historical temporary source: cursor/recursive-learning-harness-ee66
Priority: P0

Why:
The Internal AI Harness currently has a placeholder for later recurrent/looped reasoning. The Recurrent Looped Transformer (RLT) architecture — causal encoder plus all-token recurrence with carried state and sliding-window KV — is the reference pattern for a living, continuously watched recursive learning loop. Agents cannot implement that loop until the wiki, halt rules, memory banks, journal linkage, and evaluation gates are explicit.

Inputs:
- CONSTITUTION.md
- wiki/Home.md
- wiki/AI-Harness-Directive.md
- wiki/Agent-Orchestration.md
- wiki/Watcher-Directive.md
- wiki/Architecture.md
- wiki/Data-Contracts.md
- wiki/Prediction-Journal.md
- wiki/Testing-Directive.md
- RLT technical report (2026-09-12): https://yifanzhang-pro.github.io/recurrent-looped-tranformer/
- Operator screenshot of the RLT encoder / all-token-recurrence diagram

Allowed write scope:
- wiki/**
- packages/contracts/recursive/**
- tests/contracts/**
- AGENTS.md
- README.md
- .cursor/rules/recursive-learning.mdc

Forbidden write scope:
- CONSTITUTION.md
- any production model weights or live execution path
- adapters/freqtrade implementation (docs citations only)
- real-trade or order-routing code

Dependencies:
- Existing constitution and Phase 0 wiki
- Accepted ForecastPackage / MarketStateSnapshot / Hypothesis contracts

Implementation requirements:
1. Map RLT encoder + all-token recurrence onto AVAX Context Engine + Internal AI Harness without replacing the deterministic Context Engine.
2. Define bounded loop depth, halt criteria, three memory banks, and the same state transition for live / replay / training.
3. Make every loop trace journaled before outcomes are known.
4. Give Agent 00 a recursive watcher protocol and ready-to-copy task contracts for lanes 25-30 plus supporting QA.
5. Add versioned JSON schemas and contract tests.
6. Update existing directives so agents discover RLH from Home, Architecture, Harness, Watcher, Testing, and the roadmap.

Acceptance tests:
- command: python3 tests/contracts/test_recursive_schemas.py
  expected: all schema/example fixtures pass; no Constitution edit
- command: grep -R "Recursive-Learning-Harness" wiki/Home.md wiki/Architecture.md wiki/AI-Harness-Directive.md wiki/Watcher-Directive.md wiki/Build-Roadmap.md
  expected: RLH is linked from those pages
- docs: every new schema field has a leakage, halt, and journal rule

Metrics gate:
- baseline: harness loop is an undocumented future idea
- required result: implementable contracts exist; no accuracy claim is introduced

Historical regressions:
- September 2026 AVAX failed-breakout replay must remain a required RLH fixture
- 5m loop steps must not be allowed to overwrite 4H encoder memory

Docs to update:
- wiki/Home.md and all subsystem directives listed in the finish report

Finish criteria:
Wiki + schemas + tests + watcher protocol + first agent batch are merged-ready. Agents 00 and 25-30 can be launched from Recursive-Agent-Batch.md without inventing memory, halt, or journal semantics.
```

Watcher owner: Agent 00
Review mode: strict-schema
Competing task group: none
Integration dependency: none
