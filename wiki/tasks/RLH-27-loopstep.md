# RLH-27 — Same-transition LoopStep

```md
Task: Implement one D_φ LoopStep for ingest and emit, with halt budget and journal stub.
Agent: 27
Base: latest main
Integration target: main
Registered temporary source: cursor/agent-27-rlh-loopstep-ee66
Model: Grok 4.6
Priority: P0

Why:
Prompt/response boundary must not grow a cheat path. Live and replay must share the transition.

Inputs:
- wiki/Recursive-Loop-Spec.md
- packages/contracts/recursive/loop-step.schema.json
- packages/contracts/recursive/loop-trace.schema.json
- packages/contracts/recursive/halt-decision.schema.json

Allowed write scope:
- services/harness/loop/**
- tests/harness/loop/**

Forbidden write scope:
- CONSTITUTION.md
- services/harness/loop/challenge/**
- services/harness/encoder/**
- Forecast Engine numeric heads
- UI

Dependencies:
- EncoderMemory schema (accepted). Code against the schema, not Agent 26's unmerged tree.

Implementation requirements:
1. One loop_step() function for observed tokens and generated tokens.
2. Required order for directional synthesis: ENCODE_CHECK → … → HALT → JOURNAL.
3. NO_CHANGE shortcut after encode/retrieve/synthesize when 5m is immaterial.
4. max_depth default 8; halt reason typed.
5. harness_version string on every step.
6. Register a step-handler hook so Agent 28 can add CHALLENGE without editing your core file if possible; do not implement challenge logic.
7. Exact replay of a fixture trace must match content_hash when tools are deterministic.

Acceptance tests:
- required step order
- NO_CHANGE on a tiny synthetic immaterial candle
- max_depth halt fires
- live vs exact replay hash match on a synthetic trace

Finish criteria:
Versioned LoopStep + journal writer stub + tests/harness/loop.
```
