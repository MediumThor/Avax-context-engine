# WAVE2-00 — Longer live 5m lookback for 1d/1w charts

## Scope

First live Binance Vision pull was 10 days (~10 daily bars, ~1 weekly). Chart TF switcher could not show a usable 1w pane. Pull 90 days by default (env-clamped 10–180) and size chart source lookback to `days * 288` 5m bars. Incremental refresh unchanged. Metrics/snapshot stay at 8000 so `/market` stays fast.

## Files

- `services/api/runtime.py`
- `.env.example`
- `tests/test_live_htf_lookback.py`
- `wiki/Operability-Directive.md`

## Tests

- first pull calls `iter_recent_days(..., 90)` by default
- invalid env days clamp
- `_chart_by_timeframe` on 90 days of 5m yields many 1d and ≥10 1w closed buckets
- incremental path still uses `start=`

## Finish criteria

- 1d/1w panes can show months of closed buckets when the store has them
- No fixture fallback
- No execution
- No promotion
