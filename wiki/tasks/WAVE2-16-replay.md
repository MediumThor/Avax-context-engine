# WAVE2-16 — Context Engine snapshot persistence and historical replay

```md
Task: Deterministic Context Engine snapshot persistence and point-in-time historical replay
Agent: 16
Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: context-engine-wave2
Integration dependency: packages/context_engine/engine.py (PR 8 / Agent 09 — import-only)
Branch: cursor/wave2-16-replay-d941
Base: latest origin/main (b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7 at branch cut)
Priority: P0
Dependency gate: G3 (context replay)

Why:
UI, forecast, analog search, and the AI harness need a “what was known then”
query. The same raw 5m series plus engine/schema version must rebuild the same
snapshot and transition sequence. Higher-timeframe regime must not be silently
overwritten by unfinished parents or 5m relief.

Inputs:
- CONSTITUTION.md (immutable)
- wiki/Context-Engine-Directive.md
- wiki/Testing-Directive.md
- wiki/Data-Contracts.md (MarketStateSnapshot / fingerprint targets)
- wiki/Market-State-Spec.md (parent/child semantics)
- packages/context_engine/engine.py, models.py, resample.py (read-only)

Allowed write scope:
- packages/context_engine/replay.py
- tests/test_replay.py
- wiki/tasks/WAVE2-16-replay.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- packages/context_engine/__init__.py
- packages/context_engine/zones.py, fibonacci.py, thesis.py, cross_market.py, pivots_atr.py
- packages/contracts/recursive/**
- packages/models/baselines.py
- packages/journal/journal.py
- services/harness/**
- services/api/**
- apps/web/**

Assumptions:
- ContextEngine.build_snapshot is the sole state builder; replay filters first
  and does not reimplement regime/zone/pivot logic.
- A 5m bar is knowable at T only when is_closed is true AND period end
  (open_time + 5 minutes) is <= T. Unfinished and incomplete parent buckets
  are ignored (engine resample_closed already drops partial parents).
- Engine already applies parent context; replay preserves that and tests that
  a 5m relief sequence does not flip a closed 4H bearish parent.
- All timestamps are timezone-aware and normalized to UTC.
- No network and no live exchange calls.
- Persistence is an in-memory, content-addressed canonical JSON record
  (engine_version + schema_version + sha256). No SQLite/schema-owner change.
- Replay does not claim forecast accuracy and does not train models.

Implementation requirements:
1. Import and call ContextEngine; never modify it.
2. Filter candles before build_snapshot so as_of T sees only closed bars with
   period end <= T.
3. Persist snapshots in deterministic, hashable canonical JSON including
   engine_version and schema_version.
4. Replay of the same raw 5m series is byte-stable and equality-stable.
5. Mutating candles after T must not change the snapshot at T.
6. Higher-TF state comes only from completed parents.
7. Unfinished / partial parent candles are ignored.
8. UTC-aware timestamps only.

Acceptance tests (tests/test_replay.py):
- deterministic replay: same candles => same snapshots (equality + bytes)
- unfinished candle does not mutate the as_of snapshot
- perturb candles after T; snapshot at T unchanged
- point-in-time query returns only information knowable at T
- 5m relief does not overwrite a completed 4H bearish parent regime
- engine/schema version is recorded on persisted snapshots

Test commands:
- python -m pytest -q tests/test_replay.py
- python -m pytest -q tests/test_context_engine.py tests/test_leakage.py

Metrics gate:
- none (no forecast/accuracy claims)

Historical regressions:
- not the September 2026 fixture in this increment (no extra files allowed);
  4H-parent vs 5m-relief is the local hierarchy regression.

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-16-replay.md only (this contract). Context-Engine-Directive
  already states deterministic rebuild and parent/child rules.

Completion report must contain:
- files changed
- tests run and results
- no metrics/accuracy claims
- limitations
- recommended next task
- whether any contract/schema changed

Finish criteria:
- replay.py exposes snapshot_as_of / replay / persist without editing engine.py
- all six replay tests pass
- test_context_engine.py and test_leakage.py still pass
- branch committed and pushed; no GitHub PR opened (Watcher opens it)
- no merge; no forecast-accuracy claims
```

## Completion

Status: implemented on `cursor/wave2-16-replay-d941`. Watcher opens the PR.

Files:
- `packages/context_engine/replay.py`
- `tests/test_replay.py`
- `wiki/tasks/WAVE2-16-replay.md`

Tests (`python -m pytest -q tests/test_replay.py tests/test_context_engine.py tests/test_leakage.py`): 12 passed.

No `packages/contracts/**` change. Persistence is content-addressed canonical JSON, not a durable store.
