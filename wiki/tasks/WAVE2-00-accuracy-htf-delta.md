# WAVE2-00 — Accuracy dest HTF vs drift20 (research)

## Scope

Show `baseline.htf_regime_drift.v1` walk-forward MAE next to incumbent `baseline.drift20` on the Accuracy dest. Research only. Do not journal HTF live. Do not set `promotion_allowed`.

## Files

- `services/api/runtime.py` — run `walk_forward_htf_regime` when `include_challenger=True`
- `apps/web/src/api/types.ts`
- `apps/web/src/accuracy/fromMarket.ts`
- `apps/web/src/components/AccuracyPanel.tsx`
- `apps/web/src/App.tsx` — keep Accuracy dest challenger metrics if they arrive before market
- `apps/web/src/views/AccuracyView.tsx`
- `tests/test_metrics_htf_regime.py`
- `wiki/Simulation-Accuracy.md`

## Assumptions

- HTF helper already exists on main (`packages/models/htf_regime_drift.py`)
- Fixture walk-forward (~0.3s) is acceptable on the Accuracy dest only
- Live emit stays `baseline.drift20`
- Existing journal rows are not rewritten

## Tests

- `tests/test_metrics_htf_regime.py` mocks both walk-forwards
- Existing `tests/test_metrics_challenger_q50.py` still passes
- `promotion_allowed` remains false

## Finish criteria

- Accuracy dest shows HTF MAE and signed `htf_delta` vs drift20
- `/market` does not run HTF walk-forward
- No promotion claim
