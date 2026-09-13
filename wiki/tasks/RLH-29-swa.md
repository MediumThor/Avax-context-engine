# RLH-29 — SWA memory

```md
Task: W-sized sliding-window KV and merge that prefers EncoderMemory on fact conflicts.
Agent: 29
Branch: cursor/agent-29-rlh-swa-ee66
Model: Grok 4.6
Priority: P0

Why:
Unbounded prose memory is how loops invent structure.

Inputs:
- wiki/Recursive-Memory-Model.md
- packages/contracts/recursive/loop-step.schema.json

Allowed write scope:
- services/harness/memory/**
- tests/harness/memory/**

Forbidden write scope:
- CONSTITUTION.md
- deleting evicted steps from a LoopTrace
- packages/contracts/recursive/**

Implementation requirements:
1. Ring buffer W default 16, research 32.
2. Window length never exceeds W.
3. Evicted steps remain if a LoopTrace.steps list is passed in; SWA only drops them from the hot window.
4. merge(query, encoder_memory, swa, state): facts/regimes/zones/probabilities read encoder; recent reasoning reads SWA; conflicts → encoder wins + contradiction event.
5. Per-step swa_in_hash / swa_out_hash helpers.

Acceptance tests:
- window length ≤ W after many appends
- evicted entries still in provided trace.steps
- fact conflict prefers EncoderMemory
- replay of append sequence reconstructs identical hashes

Finish criteria:
SWA + merge tests green.
```
