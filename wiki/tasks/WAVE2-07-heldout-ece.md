# WAVE2-07 — Held-out ECE on live/non-fixture data

See [`.cursor/plans/heldout-ece.task.md`](../../.cursor/plans/heldout-ece.task.md) for the full contract.

Agent 07. Branch `cursor/heldout-live-ece-5716`. Source `main` `762e7b2`.

## Current

`walk_forward_probabilities` and `score_journaled_forecasts` emit ECE on the same chronological pool used to form empirical P(up), including the September fixture when n ≥ 15. That is not an unseen live calibration score.

## Required

1. Stamp `candle_source` on new journal payloads (`fixture` | `binance-vision`).
2. Report ECE only on the later 40% of live-eligible matured pairs, and only when that slice has n ≥ 15.
3. Fixture / unknown / short held-out windows leave `ece` null with `reason`.
4. `promotion_allowed` stays false.

## Forbidden

Do not rewrite `baselines.py`, recursive contracts, or PR 55 UI files. Do not fabricate ECE. Do not promote the research quantile path.

## Completion evidence (branch `cursor/heldout-live-ece-5716`)

- Candidate SHA: `b342932`
- `python3 -m pytest -q`: **318 passed**, 3 skipped
- Constitution integrity: pass
- Fixture market `/api/v1/market` ECE is null; live held-out ECE is defined only when the later 40% has n ≥ 15
- `promotion_allowed` remains false
- PR 55 paths untouched
