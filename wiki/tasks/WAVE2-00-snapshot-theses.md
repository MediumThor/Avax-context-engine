# WAVE2-00 — Thesis ledger on live snapshots

```md
Task: Rebuild competing bull/bear theses inside ContextEngine.build_snapshot with invalidation frozen at open.
Agent: 00
Branch: cursor/engine-theses-8771
Priority: P0
Source main commit: c9a56c2
Dependency gate: G3 Context

Why:
Constitution §3 requires explicit confirmation/invalidation before later candles. The ledger existed but did not drive snapshots or the UI.

Forbidden:
- CONSTITUTION.md
- moving invalidation on an existing version
- 5m observations closing a 4h thesis
- fabricated confidence
```
