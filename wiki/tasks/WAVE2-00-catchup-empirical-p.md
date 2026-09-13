# WAVE2-00 — Empirical P(up) on catch-up/drain drift20 rows

## Scope

Catch-up/drain journaled `baseline.drift20` with `p_close_above_origin` null, so those rows could never produce held-out Brier/ECE. Attach leakage-safe `empirical_signed_base_rate.v1` when the sign bucket has enough matured pairs. Do not change the drift20 point path. Do not emit an extra quantile. Do not rewrite `baselines.py`. Do not rewrite existing journal rows.

## Files

- `packages/models/direction_cal.py`
- `packages/models/__init__.py`
- `services/api/runtime.py`
- `tests/test_catchup_empirical_p.py`
- `tests/test_shadow_journal.py`
- `tests/test_shadow_journal_drain.py`
- `wiki/Prediction-Journal.md`

## Assumptions

- Prefix-only history at the catch-up origin (no later bar).
- Live stamp remains `binance-vision` via `_with_data_source`.
- `promotion_allowed` stays false.
- Existing null-p rows stay append-only.

## Tests

- `emit_baseline_forecast` still emits null p
- Attach fills p from prefix; later candles do not change that prefix p
- Attach does not overwrite an existing p
- Live-stamped drain rows can produce held-out live Brier when n ≥ MIN_BRIER

## Finish criteria

- Drain/catch-up rows may carry honest P(up)
- No quantile emit on the drain path
- No promotion
