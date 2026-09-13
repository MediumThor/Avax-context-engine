# Recursive Evaluation

Extra loop depth is an experiment. This page defines how to prove it helped, or stop doing it.

## What is being measured

Not "did the model become superintelligent." Measured questions:

1. Did the loop respect encoder facts and invalidations?
2. Did more depth change the structured analysis, and was that change beneficial after outcomes matured?
3. Did the loop leak future information?
4. Did live and replay match?
5. Did latency / cost stay inside budget?
6. Did 5m steps overwrite higher-timeframe readings?

Forecast numeric quality still uses [`Simulation-Accuracy.md`](Simulation-Accuracy.md). RLH adds **process quality** and **depth ablation**.

## Fixtures

Every harness eval case is a frozen directory:

```text
benchmarks/rlh/<fixture_id>/
  manifest.json
  candles.jsonl          # includes future, hidden at as_of
  encoder_memory.json
  forecast_package.json
  expected_invariants.json
  notes.md
```

Required fixtures:

| id | purpose |
| --- | --- |
| `avax-2026-09-failed-8` | founding dogfood: failed ~$8 breakout, relief bounce must not reset 4H bear. `candles.jsonl` is sealed; later bars stay hidden at `as_of`. |
| `no-change-5m` | immaterial 5m candle → `NO_CHANGE` halt |
| `stale-data` | health stale → degraded halt, no confident forecast language |
| `invalidation-already-fired` | loop must close/respect thesis, not move the level |
| `model-disagreement` | confidence_source = model-disagreement, wide uncertainty restated |
| `parent-child-split` | 4H bear + 5m bounce language test |
| `analog-cutoff` | analog.search refuses post-`as_of` hits |
| `replay-parity` | live hash equals exact replay hash |

Agents 36-39 may add fixtures. They may not delete these.

## Process metrics (blocking)

Computed on the journaled `LoopTrace` before looking at future prices:

- `encode_check_present`
- `challenge_present` for any directional synthesis
- `halt_present`
- `citations_cover_claims`
- `no_uncalibrated_percent`
- `no_invented_zone`
- `no_invented_probability`
- `parent_regime_not_overwritten`
- `tool_as_of_respected`
- `exact_replay_match` on `rebuild_policy=exact`

A fixture can fail process metrics even if the eventual price move "agreed" with the prose.

## Depth ablation

**Implemented:** `services/evaluator/rlh/depth.py` (`ablate_depths`) — see [`tasks/RLH-06-depth-ablation.md`](tasks/RLH-06-depth-ablation.md).

For traces that emitted a structured analysis at more than one prefix (or that can be replayed with `max_depth ∈ {1,2,4,8,16}`):

Record per depth:

- process metrics;
- whether `NO_CHANGE` would have been correct;
- after outcomes mature: Brier / MAE / coverage **of the ForecastPackage** (unchanged by depth) plus **explanation-alignment** scores below;
- latency and tool-call count.

Explanation-alignment (post-outcome, never used as a fake probability):

- `invalidation_called_correctly` — did the loop say a thesis was dead when the ledger said so;
- `relief_vs_reversal` — binary judge against fixture labels, not against future profit;
- `uncertainty_language_ok` — disagreement/stale data not described as high conviction.

If depth 8 fails process metrics that depth 4 passed, depth 8 is worse. Do not average that away.

## Outcome-linked scores

When horizons mature, attach `LoopOutcome`:

- copy horizon scores from the evaluator for the bound `forecast_id`;
- `depth_prefix_scores` if prefixes exist;
- `challenge_respected_invalidation`;
- `parent_regime_preserved`;
- `leakage_probe_passed`.

RLH cannot "beat" a baseline by changing the ForecastPackage after the fact. If a loop wants a different ensemble, that is a **new experiment** in the Forecast Engine, journaled as a new package.

## Leakage probes

Agents 36 must run, on every integration candidate:

1. Future-candle perturbation at `T`.
2. Unfinished parent-candle injection.
3. Analog post-cutoff bait documents.
4. Warm-start that illegally contains `T+` outcomes.
5. Tool call with missing `as_of` (must refuse).

Any fail blocks promotion.

## Statistical caution

A handful of traces do not justify raising `max_depth`. Report:

- fixture count;
- window;
- halt-reason mix;
- replay mismatch count;
- latency p50/p95;
- process-metric pass rate;
- depth-ablation table.

Watcher rejects "the loop felt smarter."

## Promotion gate (harness)

A challenger `harness_version` may replace the incumbent only if it:

- passes all required fixtures' process metrics;
- does not regress September 2026 parent-regime preservation;
- does not increase replay mismatches;
- does not worsen stale-data behavior;
- stays inside latency budget;
- shows a predeclared improvement on a **predeclared** fixture set (example: fewer false reversals on relief-bounce fixtures) without buying that gain by skipping `CHALLENGE`.

When indistinguishable, keep the shallower, cheaper, more exact harness.

## Continuous monitor

Once shadow-live exists, scheduled Agent 00 / 38 jobs inspect new matured traces:

- rolling process-metric pass rate;
- halt-reason drift (`max_depth` becoming the majority is a smell);
- contradiction rate;
- tool refusal rate;
- replay canary on a sampled live `as_of`.

Alerts become tasks. One ugly forecast does not retrain the loop.
