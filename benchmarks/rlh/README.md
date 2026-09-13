# RLH fixtures

Frozen Recursive Learning Harness evaluation cases. Labels are about process invariants, not hindsight-perfect trades.

See `wiki/Recursive-Evaluation.md`. Required fixture IDs must not be deleted.

Each required fixture directory contains:

| file | role |
| --- | --- |
| `manifest.json` | fixture_id, purpose, as_of, promotion_allowed, artifact presence |
| `expected_invariants.json` | blocking process labels (not numeric scores) |
| `notes.md` | human-readable scenario and expected loop behavior |
| `candles.jsonl` | frozen candles; future bars hidden at `as_of` |
| `encoder_memory.json` | encoder snapshot at `as_of` |
| `forecast_package.json` | bound ForecastPackage (unchanged by depth) |
| `loop_trace.json` | journaled LoopTrace scored by `services/evaluator/rlh/runner.py` |

## Required fixtures

| fixture_id | status |
| --- | --- |
| `avax-2026-09-failed-8` | sealed candles; loop trace TODO |
| `no-change-5m` | stub |
| `stale-data` | stub |
| `invalidation-already-fired` | stub |
| `model-disagreement` | stub |
| `parent-child-split` | stub |
| `analog-cutoff` | stub |
| `replay-parity` | stub |

`avax-2026-09-failed-8/candles.jsonl` is sealed (`manifest.json` status=`sealed`, sha256 recorded). Future candles stay in the dump and must stay hidden at `as_of`.

## Runner (fail closed)

```bash
pytest tests/rlh
```

`run_fixture_dir` loads `expected_invariants.json` and, when present, `loop_trace.json`. If blocking invariants require a scored trace and `loop_trace.json` is missing, status is `incomplete` (or `invariants_only` when no trace is required) and **`passed` is always false**. Process metrics never invent forecast accuracy.

Stubs lock IDs and expected invariants so implementation agents do not invent new goalposts.
