# WAVE2-00 — Held-out live ECE slice

**Agent:** 00 Watcher
**Branch:** `cursor/journal-live-ece-8771`
**Status:** implemented

## Why

Constitution and Simulation-Accuracy require held-out ECE on live data. Journal scores previously pooled fixture and live rows, so fixture ECE could be read as live calibration.

## Files

- `packages/models/journal_scores.py`
- `services/api/runtime.py`
- `apps/web/src/api/types.ts`
- `apps/web/src/accuracy/fromMarket.ts`
- `apps/web/src/components/AccuracyPanel.tsx`
- `tests/test_journal_live_ece.py`
- `wiki/tasks/WAVE2-00-journal-live-ece.md`

## Assumptions

- New journal writes stamp `data_source` (`fixture` or `binance-vision`). Existing rows stay untagged = unknown, not live.
- Live ECE/Brier require the same MIN_ECE / MIN_BRIER gates. Missing stays not yet scored.
- Not a promotion.

## Tests

- fixture + untagged rows do not produce live ECE even when pooled ECE exists
- binance-vision rows with n ≥ MIN_ECE produce live ECE
- fixture persist stamps `data_source=fixture`

## Finish

Accuracy dest can show held-out live ECE as not yet scored until live journal rows exist. Fixture ECE is not live ECE.
