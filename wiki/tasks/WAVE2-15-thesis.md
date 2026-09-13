# WAVE2-15 — Immutable thesis ledger

```md
Task: Implement immutable-versioned bull/bear thesis objects. Once invalidation triggers, close the thesis; do not move its invalidation.
Agent: 15
Branch: cursor/agent-15-thesis-ledger-5f27
Priority: P0

Why:
Constitution §3 forbids moving goalposts. An active thesis must carry explicit confirmation and invalidation before later candles arrive. After an invalidation fires, agents may not rewrite that version's levels to preserve a prior narrative. The September 2026 AVAX ~$8 failed-breakout episode is the permanent regression for this failure mode: a later relief bounce must not rewrite a fired bear invalidation.

Inputs:
- CONSTITUTION.md (§3 no moving goalposts, §18 September regression)
- wiki/Context-Engine-Directive.md (thesis ledger)
- wiki/Data-Contracts.md (Hypothesis)
- wiki/Prediction-Journal.md (append-only / no hindsight overwrite)
- wiki/Market-State-Spec.md (September expected behavior)
- wiki/Testing-Directive.md (thesis invalidation; do not move bullish invalidation lower)
- benchmarks/rlh/avax-2026-09-failed-8/expected_invariants.json (read-only spirit; do not edit prices)

Allowed write scope:
- packages/context_engine/thesis.py
- tests/test_thesis.py
- wiki/tasks/WAVE2-15-thesis.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- services/harness/**
- apps/web/**
- changing September fixture invalidation prices
- packages/contracts/recursive/**

Dependencies:
- Accepted Hypothesis contract in wiki/Data-Contracts.md
- No overlap with WAVE2-00 harness paths or PR 8 engine/API/UI files

Implementation requirements:
1. Hypothesis fields: evidence, counter_evidence, confirmation_rules, invalidation_rules, status, version (plus contract identity/closure fields).
2. invalidation_rules are immutable for a version. Changed reasoning closes the old version and opens a new one.
3. Attempting to mutate invalidation on an active thesis fails or is rejected.
4. Close-on-fire: when an invalidation rule is met, the thesis is closed; its rules stay frozen.
5. September 2026 spirit: a 5m/15m relief bounce must not rewrite a fired bear invalidation (failed-breakout reclaim level stays put).
6. 5m observations evaluate only 5m rules; they must not silently satisfy or rewrite a higher-timeframe invalidation.

Acceptance tests:
- command: python -m pytest -q tests/test_thesis.py
  expected: all tests pass
- mutate invalidation on an active thesis raises ImmutableInvalidationError
- fire closes the thesis and leaves invalidation_rules unchanged
- revise() closes the prior version and increments version
- September relief-bounce case does not alter a fired bear invalidation price
- benchmarks/rlh/avax-2026-09-failed-8/expected_invariants.json unchanged

Metrics gate:
- baseline: no thesis ledger module
- required result: deterministic ledger + tests; no forecast accuracy claim

Historical regressions:
- September 2026 AVAX failed breakout / relief bounce must not move or revive a fired bear invalidation

Docs to update:
- wiki/tasks/WAVE2-15-thesis.md (this contract)

Finish criteria:
thesis.py + test_thesis.py + this contract exist on the branch; pytest tests/test_thesis.py is green; invalidation cannot be moved on an active or closed version; close-on-fire works; September spirit test passes without editing fixture prices.
```

Watcher owner: Agent 00
Review mode: strict-schema
Competing task group: none
Integration dependency: none
