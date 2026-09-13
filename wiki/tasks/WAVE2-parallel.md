# WAVE-2 parallel batch (non-overlapping with RLH core and PR 8)

Watcher 00 owns `services/harness/**` on `cursor/watcher-wave2-rlh-core-8771`.
PR 8 owns `apps/web/src/App.tsx`, `services/api/main.py`, `packages/models/baselines.py`, `packages/journal/journal.py`, `packages/context_engine/engine.py`.

Launch these from **latest `main`**. Do not touch locked paths.

| agent | task | allowed write scope |
| --- | --- | --- |
| 03 | leakage-safe feature assembler | `packages/features/**`, `tests/features/**` |
| 06 | chronological walk-forward | `packages/evaluator/walkforward.py`, `tests/test_walkforward.py` |
| 07 | calibration / ECE | `packages/evaluator/calibration.py`, `tests/test_calibration.py` |
| 10 | ATR/zigzag second pivot method | `packages/context_engine/pivots_atr.py`, `tests/test_pivots_atr.py` |
| 11 | zone probe/accept/reclaim lifecycle | `packages/context_engine/zones.py`, `tests/test_zones.py` |
| 12 | structural Fibonacci | `packages/context_engine/fibonacci.py`, `tests/test_fibonacci.py` |
| 14 | BTC/ETH relative context | `packages/context_engine/cross_market.py`, `tests/test_cross_market.py` |
| 15 | immutable thesis ledger | `packages/context_engine/thesis.py`, `tests/test_thesis.py` |
| 16 | deterministic snapshot replay | `packages/context_engine/replay.py`, `tests/test_replay.py` |
| 02 | FreqAI bootstrap/adapter only | `adapters/freqtrade/**`, `scripts/bootstrap_freqtrade.sh` |
| 20 | ForecastFan component only | `apps/web/src/components/ForecastFan.tsx` |
| 08 | OSS research log | `wiki/Open-Source-Research-Log.md` |
| 35 | benchmark registry | `benchmarks/registry/**` |
| 37 | journal replay red team | `tests/replay/**` |

Forbidden for every agent: `CONSTITUTION.md`, `packages/contracts/recursive/**`, PR 8 paths, `services/harness/**`.

Live roster: `artifacts/watcher/active-tasks.json`. Watcher review board: `wiki/tasks/WAVE2-00-watch.md`.
