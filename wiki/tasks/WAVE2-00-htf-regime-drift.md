# WAVE2-00 — HTF-gated drift research baseline

**Agent:** 00 Watcher
**Branch:** `cursor/htf-regime-drift-8771`
**Status:** implemented — research only

## Why

Constitution §2 ranks higher-timeframe regime above 5m quantitative drift. `baseline.drift20` will project a 5m relief bounce even after three closed 4h declines. This helper gates that drift. It does not replace the live journaled model.

## Files

- `packages/models/htf_regime_drift.py`
- `packages/models/__init__.py`
- `tests/test_htf_regime_drift.py`
- `wiki/Simulation-Accuracy.md`
- `wiki/tasks/WAVE2-00-htf-regime-drift.md`

## Assumptions

- Parent regime is three consecutive closed 4h closes. Incomplete HTF buckets are dropped.
- Live forecast emit stays `baseline.drift20` / research quantiles. This path is not journaled.
- `promotion_allowed` stays false even if walk-forward MAE is lower.

## Tests

- synthetic 4h decline + 5m bounce → gated path is 0 while drift20 is positive
- as_of prefix ignores a later completed 4h bar
- fixture walk-forward never sets promotion

## Fixture walk-forward (research only)

September 2026 fixture, chronological origins, `min_history=200`, `step=40`, n=89 per horizon. HTF-gated MAE was below both `baseline.drift20` and `baseline.zero` on h=1..10. Example h=1: htf 0.000024, drift20 0.000026, zero 0.000078. h=10: htf 0.000019, drift20 0.000046, zero 0.000565.

This is **not a promotion**. One sealed fixture is not held-out live ECE. Live emit stays unchanged until a Watcher-accepted evaluation plan says otherwise.

## Finish

Research scorer exists. Not a promotion. Do not change live emit until it beats drift20 OOS on a frozen plan and Watcher accepts it.
