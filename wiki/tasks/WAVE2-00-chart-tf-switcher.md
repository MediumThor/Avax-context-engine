# WAVE2-00 — Chart timeframe switcher

**Agent:** 00 Watcher
**Branch:** `cursor/chart-tf-switcher-8771`
**Status:** implemented

## Why

UI Directive and Navigation Directive require clicking a timeframe to change chart granularity without erasing the higher-timeframe hierarchy. The Market dest was 5m-only; `?tf=` was specified but unused.

## Files

- `apps/web/src/nav/destinations.ts`
- `apps/web/src/App.tsx`
- `apps/web/src/api/types.ts`
- `apps/web/src/styles.css`
- `services/api/runtime.py`
- `services/api/main.py`
- `tests/test_chart_tf_switcher.py`
- `tests/test_mobile_dest_nav.py`
- `wiki/Navigation-Directive.md`
- `wiki/UI-Directive.md`
- `wiki/tasks/WAVE2-00-chart-tf-switcher.md`

## Assumptions

- Resample only closed 5m bars already truncated at `as_of`.
- Incomplete HTF buckets are dropped (`resample_closed`).
- `candles` stays the 5m pane so existing volume/breakout tests hold.
- Forecast remains next-10 5m candles. Not a promotion.

## Tests

- invalid `tf` degrades to 5m
- payload includes resampled 15m/1h/4h/1d/1w
- future 5m mutation after `as_of` does not change 4h chart candles
- dest URL encodes `tf` when not 5m

## Finish

Operator can switch 5m→1w on Market/Replay. HTF zones remain. No execution. No fabricated ECE.
