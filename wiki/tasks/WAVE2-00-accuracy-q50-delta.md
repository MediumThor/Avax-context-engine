# WAVE2-00 — Surface q50 MAE vs drift20 on Accuracy

**Agent:** 00 Watcher
**Branch:** `cursor/accuracy-q50-delta-8771`
**Status:** implemented — awaiting PR

## Why

The live forecast can be a research quantile envelope, but Accuracy dest only showed drift20/zero point error. Walk-forward q50 vs `baseline.drift20` already exists and was not on the market metrics payload.

## Files

- `services/api/runtime.py`
- `tests/test_metrics_challenger_q50.py`
- `apps/web/src/api/types.ts`
- `apps/web/src/accuracy/fromMarket.ts`
- `apps/web/src/components/AccuracyPanel.tsx`
- `apps/web/src/views/AccuracyView.tsx`
- `wiki/Simulation-Accuracy.md`
- `wiki/tasks/WAVE2-00-accuracy-q50-delta.md`

## Assumptions

- `promotion_allowed` stays false even if q50 MAE is lower on some horizons.
- Missing q50 stays not yet scored. No invented ECE.
- Walk-forward uses chronological origins only (existing helper).

## Tests

- fixture metrics include q50 MAE and q50-minus-drift20
- promotion_allowed is false
- future-bar perturbation does not change the attached q50 MAE

## Finish

Accuracy dest shows challenger q50 vs drift20. Not a promotion.
