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

Stubs below lock the IDs and expected invariants so implementation agents do not invent new goalposts.
