# WAVE2-00 — Multi-round shadow-journal drain

**Agent:** 00 Watcher
**Branch:** `cursor/journal-empty-rounds-8771`
**Status:** implemented — awaiting PR

## Scope

One Journal drain can run several bounded drift20 catch-up rounds so remaining can reach 0 without a quantile emit.

## Files

- `services/api/runtime.py`
- `services/api/main.py`
- `tests/test_shadow_journal_drain.py`
- `apps/web/src/api/market.ts`
- `apps/web/src/api/types.ts`
- `apps/web/src/components/ShadowJournalCard.tsx`
- `wiki/Prediction-Journal.md`
- `wiki/tasks/WAVE2-00-journal-empty-rounds.md`

## Assumptions

- Per-round budget stays ≤500.
- Rounds capped at 25.
- Kill switch still 423 / wrote=0.
- Existing quantile rows are not rewritten.

## Tests

- rounds=3 writes more than rounds=1 when remaining is large
- no extra quantile rows
- kill switch still blocks

## Finish

Remaining can be drained to 0 in one operator action. Not a promotion.
