# WAVE2-00 — Benchmarks and Models secondary dests

**Agent:** 00 Watcher
**Branch:** `cursor/benchmarks-models-dest-8771`
**Status:** implemented

## Why

Navigation Directive names `/benchmarks` and `/models`. The five-dest phone nav stays Market / Replay / Accuracy / Health / More. These two are secondary dests from More.

## Files

- `apps/web/src/nav/destinations.ts`
- `apps/web/src/views/{Benchmarks,Models,More}View.tsx`
- `apps/web/src/api/catalog.ts`
- `apps/web/src/App.tsx`
- `services/api/{catalog,main}.py`
- `tests/test_benchmarks_models_dest.py`
- `wiki/Navigation-Directive.md`
- `wiki/tasks/WAVE2-00-benchmarks-models-dest.md`

## Assumptions

- Registry payload names gates only. No invented ECE/MAE.
- Incumbent remains `baseline.drift20`. Research rows stay unpromoted.
- Bottom nav still has exactly five dests.

## Tests

- DEST_IDS unchanged
- `/api/v1/benchmarks` lists draft entries without score fields
- `/api/v1/models` incumbent drift20, promotion_allowed false

## Finish

Operator can open /benchmarks and /models from More. Not a promotion.
