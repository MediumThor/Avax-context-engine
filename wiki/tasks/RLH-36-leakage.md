# RLH-36 — Leakage red team

```md
Task: Five blocking leakage probes for RLH encoder/loop memory.
Agent: 36
Branch: cursor/agent-36-rlh-leakage-ee66
Model: Grok 4.6
Priority: P0

Why:
A recursive loop that can see T+1 is worse than a dumb baseline.

Inputs:
- wiki/Recursive-Evaluation.md (Leakage probes)
- wiki/Testing-Directive.md
- packages/contracts/recursive/examples/encoder-memory.example.json

Allowed write scope:
- tests/leakage/rlh/**

Forbidden write scope:
- CONSTITUTION.md
- services/** (you may import; do not patch production to silence a probe)
- deleting required fixtures

Implementation requirements:
Write tests (they may skip or xfail only if the implementation module is absent — never delete the probe):
1. Future-candle perturbation at T.
2. Unfinished parent-candle injection.
3. Analog post-cutoff bait.
4. Warm-start that illegally contains T+ outcomes.
5. Tool call with missing as_of must refuse.

Acceptance tests:
- python3 -m unittest discover -s tests/leakage/rlh or pytest tests/leakage/rlh
- probes exist even if harness modules are still stubs

Finish criteria:
Five named probes. No production silencing.
```
