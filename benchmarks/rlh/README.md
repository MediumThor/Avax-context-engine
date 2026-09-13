# RLH fixtures

Frozen Recursive Learning Harness evaluation cases. Labels are about process invariants, not hindsight-perfect trades.

See `wiki/Recursive-Evaluation.md`. Required fixture IDs must not be deleted.

Each fixture directory should eventually contain:

- `manifest.json`
- `candles.jsonl` (future candles present, hidden at `as_of`)
- `encoder_memory.json`
- `forecast_package.json`
- `expected_invariants.json`
- `notes.md`

`avax-2026-09-failed-8/candles.jsonl` is sealed (`manifest.json` status=`sealed`, sha256 recorded). Future candles stay in the dump and must stay hidden at `as_of`. Other fixture IDs may still be stubs. Do not invent new goalposts.
