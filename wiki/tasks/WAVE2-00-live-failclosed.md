# WAVE2-00 — Live ingest fail-closed

**Agent:** 00 Watcher
**Branch:** `cursor/live-failclosed-8771`
**Status:** implemented — awaiting PR

## Why

Phase 9 requires continuous read-only AVAX ingest. `_ensure` currently seeds the September fixture when a live Binance Vision pull fails, which can label stale/fixture data as if it were live.

## Files

- `services/api/runtime.py`
- `services/api/main.py`
- `tests/test_live_failclosed.py`
- `apps/web/src/App.tsx`
- `.env.example`
- `wiki/Operability-Directive.md`
- `wiki/tasks/WAVE2-00-live-failclosed.md`

## Assumptions

- `AVAX_USE_FIXTURE=1` still seeds the September dump.
- Live mode never writes `source=fixture`.
- Existing live bars may be served stale if a refresh fails; health uses age.
- Empty live store + failed pull → 503, not fixture.
- No execution. No quantile promotion.

## Tests

- failed first live pull does not seed fixture
- incremental refresh appends newer closed bars
- refresh failure keeps prior live bars
- `/api/v1/market/AVAXUSDT` is 503 when live is empty and pull fails

## Finish

Live ingest updates closed 5m bars. Fixture fallback is explicit env only.
