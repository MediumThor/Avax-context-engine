# Benchmark registry

Versioned catalog of **evaluation gates**. An entry names the dataset window, metrics, baselines, leakage rules, and pass/fail rules that a later model or context change must be judged against.

This directory does **not** store run scores, accuracy percentages, ECE values, or coverage numbers. Those belong in future Evaluation Engine manifests after a walk-forward is actually executed.

Authority: [`CONSTITUTION.md`](../../CONSTITUTION.md) §§5–6, 13, 16, 18. Metric names follow [`wiki/Simulation-Accuracy.md`](../../wiki/Simulation-Accuracy.md). Process regressions point at frozen RLH fixtures under [`benchmarks/rlh/`](../rlh/); this registry must not edit that tree.

## Why this exists

Without a named gate, later work can silently redefine what “better” means after seeing results (new window, swapped metric, dropped baseline, weakened leakage rule). The Watcher rejects that class of claim. See [`wiki/Watcher-Directive.md`](../../wiki/Watcher-Directive.md) and [`wiki/Continuous-Improvement-Directive.md`](../../wiki/Continuous-Improvement-Directive.md).

## Layout

```text
benchmarks/registry/
  README.md
  schema.json
  validate.py
  test_benchmark_registry.py
  entries/
    <id>.<status>.json
```

Filename MUST be `{id}.{status}.json` and MUST match the JSON `id` and `status` fields.

## Lifecycle

| status | Meaning | Mutation |
| --- | --- | --- |
| `draft` | Named gate. Window, thresholds, and data manifest may still be unspecified. | Owner may edit definitions. Must not add scores. |
| `accepted` | Watcher accepted the definition after out-of-sample evidence and a sealed window/manifest. | Locked. Changes require a **new** `id`. |
| `frozen` | Permanent regression or sealed promotion gate. Independent replication recommended (Agent 39). | Locked. Deletion is forbidden. |

`draft` is not a license to report performance. It is a license to name the task.

Promotion (`draft` → `accepted` → `frozen`) **requires Watcher (Agent 00) plus out-of-sample evidence**. In-sample fit, a single attractive backtest, or a swapped metric after results are seen is not evidence. Random time-series shuffle is prohibited.

Schema version 1 stores **no numeric thresholds**. Sealing numeric gates is a later Watcher-owned schema revision. Do not add ad-hoc score fields to draft entries.

## How to add an entry

1. Read this README, `schema.json`, and the Constitution leakage/baseline/promotion clauses.
2. Choose a new `id` (`[a-z0-9][a-z0-9.-]*`). Do not reuse an `accepted` or `frozen` id.
3. Write `entries/<id>.draft.json` with `status: "draft"`.
4. Name `dataset_id` and `time_range`. If no snapshot exists, leave `start`/`end` null and `sealed: false`. Do not invent dates or dumps.
5. List metric **names** only (for example MAE, RMSE, direction, Brier, pinball, interval coverage, calibration/ECE). No values.
6. List `baseline_ids` by name. Constitution mandatory forecast baselines: zero return, persistence/drift, EMA/trend heuristic, simple statistical classifier/regressor (Simulation-Accuracy also names logistic direction and linear return).
7. State `leakage_rules` and `validation_policy`. Forecast tasks MUST use `chronological_walk_forward` with `random_shuffle_allowed: false`.
8. Write pass/fail **rules** with `threshold_status: unset` or `not_applicable`. Do not invent cutoffs.
9. Set `owner_agent` to your lane (this catalog: `"35"`).
10. Run `python3 benchmarks/registry/validate.py`.

If the new entry points at an RLH fixture, set `dataset_ref` / `related_paths` to `benchmarks/rlh/<fixture_id>/` and **do not modify** that tree.

## What must not be redefined in place

Once `accepted` or `frozen`, these fields are the gate. Changing them is a new entry, not an edit:

- `dataset_id` / `time_range`
- `metrics`
- `baseline_ids`
- `leakage_rules`
- `validation_policy`
- `pass_fail_rules`

Silent metric substitution, cherry-picked windows, and hidden abstentions are Watcher reject reasons.

## Validation

Stdlib only. No extra JSON Schema package.

```text
python3 benchmarks/registry/validate.py
python3 -m pytest benchmarks/registry/test_benchmark_registry.py
```

Default repo `pytest` `testpaths` is `tests/`. Invoke the registry module by path so it does not collide with `tests/` names.

Manual checks if you do not run the script:

- JSON parses and matches `schema.json` required fields.
- Filename equals `{id}.{status}.json`.
- `status` is `draft`, `accepted`, or `frozen`.
- Draft entries have `time_range.sealed: false`.
- No numeric performance fields (MAE/RMSE/Brier/ECE/coverage/accuracy values, deltas, thresholds).
- `random_shuffle_allowed` is false when `validation_policy` is present.
- RLH `related_paths` exist and were not edited in the same change.

## Current draft entries

| id | kind | status | Notes |
| --- | --- | --- | --- |
| `avax-5m-next10` | forecast | draft | Core AVAX 5m next-10-candle forecast. Window unsealed. Walk-forward only. |
| `avax-2026-09-failed-8` | process_regression | draft | Pointer to the founding September 2026 failed ~$8 breakout fixture. No invented outcomes. |

## Out of scope here

- `benchmarks/rlh/**` fixture bodies (owned elsewhere; leave untouched).
- Evaluation Engine run manifests and recorded scores (Agent 06 / later).
- `LearningCandidate` / `PromotionDecision` / `LessonRecord` machine schemas (later Agent 35 + Agent 31).
- Real trade execution (forbidden in v1).
