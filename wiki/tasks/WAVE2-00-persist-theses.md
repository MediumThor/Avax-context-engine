# WAVE2-00 — Persist competing theses without moving invalidation

```md
Task: Append-only thesis ledger in the journal DB. Live snapshots freeze invalidation from the first stored version. Replay does not write.
Agent: 00
Branch: cursor/persist-theses-8771
Priority: P0
Source main commit: 6a64183

Why:
Theses were rebuilt every request. Rebuild is deterministic today, but Constitution §3/§8 require a durable versioned ledger so a later 5m bounce cannot rewrite a frozen 4h invalidation.

Allowed write scope:
- packages/journal/**
- services/api/runtime.py
- services/api/main.py
- tests/test_persisted_theses.py
- tests/test_engine_theses.py
- apps/web/src/api/types.ts
- apps/web/src/App.tsx
- wiki/**

Forbidden write scope:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py

Implementation requirements:
1. theses table is insert-only. Same id cannot change invalidation_fingerprint.
2. Live snapshot writes when persist_theses is true (default when as_of is None). Live market/forecast always pass last close as as_of, so they set persist_theses from the forecast persist flag.
3. Replay and kill switch do not insert. They still bind stored rules when a row exists.
4. GET /api/v1/theses/{id} returns the frozen row or 404.
5. September 4h bear invalidation stays 8.192 after a second persist.

Finish criteria:
Durable theses. No rewrite. No confidence. No execution.
```
