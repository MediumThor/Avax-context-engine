# WAVE2-01 — OHLCV gap / duplicate / manifest integrity

```md
Task: Add read-only gap, duplicate, OHLC, and manifest checksum helpers for immutable 5m OHLCV.
Agent: 01
Branch: cursor/wave2-01-integrity-985e
Priority: P0

Why:
Data integrity is the first layer of the Constitution truth hierarchy. Replay, features, and forecasts are invalid if the 5m grid has silent gaps, duplicate open times, or OHLC violations. Manifest checksums must match the store's canonical payload hash so live/simulated runs can cite a reproducible data snapshot.

Inputs:
- CONSTITUTION.md (immutable; no future leakage; UTC timestamps)
- wiki/Data-Contracts.md (Candle contract)
- packages/market_data/store.py (read-only: CandleStore._payload + manifest hashing)
- packages/market_data/binance.py (read-only; no live fetch in this task)
- packages/context_engine/models.py (Candle)

Allowed write scope:
- packages/market_data/integrity.py
- tests/test_data_integrity.py
- wiki/tasks/WAVE2-01-integrity.md

Forbidden write scope:
- CONSTITUTION.md
- packages/market_data/store.py (PR 8 owns writes)
- packages/market_data/binance.py except tiny import-only use
- services/harness/**
- apps/web/**

Dependencies:
- Existing CandleStore payload JSON and newline-delimited SHA-256 (do not rewrite the store)

Implementation requirements:
1. Detect missing bars versus the UTC 5m grid spanning first..last open_time.
2. Detect duplicate open_times (and conflicting payloads at the same open_time).
3. Detect OHLC violations, including non-finite prices and high/low vs open/close.
4. Manifest checksum helper must match CandleStore.manifest by importing CandleStore._payload (or duplicating the same canonical JSON).
5. Tests use synthetic gapped/duplicated/invalid series only. No trading keys. No live exchange calls required for acceptance.

Acceptance tests:
- command: python3 -m pytest tests/test_data_integrity.py -q
  expected: all tests pass
- command: python3 -m pytest tests/test_market_data.py -q
  expected: existing store immutability test still passes

Metrics gate:
- baseline: no integrity helpers
- required result: synthetic gap, duplicate, OHLC, and store-checksum cases fail closed (issues reported; checksum equality holds)

Historical regressions:
- none in this increment (helpers are series-level, not Sept-2026 fixture replay)

Docs to update:
- wiki/tasks/WAVE2-01-integrity.md (this contract + completion report)

Finish criteria:
Helpers exist, tests green, store.py untouched, no live trading credentials, PR opened to main.
```

## Public helpers

| helper | role |
| --- | --- |
| `expected_5m_grid(start, end)` | inclusive UTC 5m open times on the exchange-aligned grid |
| `find_gaps(records)` | missing aligned slots in `[first, last]` |
| `find_duplicates(records)` | repeated `open_time` values |
| `find_ohlc_violations(records)` | high/low/open/close/volume invariants |
| `canonical_payload(candle)` | `CandleStore._payload` passthrough |
| `manifest_sha256(candles)` | store-compatible checksum |
| `audit_ohlcv(records)` | combined `IntegrityReport` |

No schema owner change. Integrity reports are additive diagnostics; they do not mutate candles.

## Completion report

- **What changed:** Added read-only `packages/market_data/integrity.py` helpers for UTC 5m gap detection, duplicate `open_time`s (including conflicting payloads), OHLC/non-finite/negative-volume violations, and a manifest SHA-256 that reuses `CandleStore._payload` plus newline-delimited hashing. Store is not rewritten.
- **Files changed:**
  - `packages/market_data/integrity.py` (new)
  - `tests/test_data_integrity.py` (new)
  - `wiki/tasks/WAVE2-01-integrity.md` (this file)
- **Tests run:** `python3 -m pytest tests/test_data_integrity.py tests/test_market_data.py tests/test_leakage.py tests/test_context_engine.py tests/test_baselines.py tests/test_journal.py tests/test_evaluator.py -q` → **16 passed**.
- **Metrics before/after:** No forecasting metrics. Before: no series integrity helpers. After: synthetic contiguous series is clean; 2-bar gap, duplicate/conflict, unaligned stamp, and OHLC/NaN/negative-volume cases fail closed; checksum equals `CandleStore.manifest` on the same chronological series.
- **Known limitations:** Helpers do not fetch live Binance data (acceptance is synthetic). `Candle` construction already rejects many OHLC errors, so invalid-bar tests use raw mappings. Payload JSON is sensitive to `int` vs `float` (`100` vs `100.0`) because it delegates to `CandleStore._payload`. Unaligned bars are flagged in addition to the missing aligned slot. Empty series is `ok` with zero expected slots.
- **Documentation updated:** this task contract only (`Data-Contracts.md` unchanged; no schema owner change).
- **Contract/schema changed:** no. Additive diagnostic types only (`IntegrityIssue`, `IntegrityReport`).
- **Recommended next task:** Agent 01/34 wire `audit_ohlcv` into freshness/health so replay and `/health` surface gap counts; Agent 36 can add a leakage probe that mutates a future 5m bar and asserts the pre-`as_of` manifest is unchanged.
