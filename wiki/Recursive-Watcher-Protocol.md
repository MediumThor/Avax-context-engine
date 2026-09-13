# Recursive Watcher Protocol

This is Agent 00's specialized loop for the Recursive Learning Harness. It extends [`Watcher-Directive.md`](Watcher-Directive.md); it does not replace it.

## Why a dedicated protocol

A recurrent loop can fail in ways a one-shot explanation does not:

- silent state carry across the prompt/response boundary;
- SWA treating recent prose as if it were a candle;
- extra depth used to talk past an invalidation;
- replay divergence after a "small" prompt change;
- warm-start smuggling matured outcomes;
- 5m tokens overwriting 4H encoder slices.

Watcher treats those as first-class defects.

## Continuous watches

### Work graph

Track:

- which agent owns `packages/contracts/recursive/` (only one writer);
- active RLH implementation branches (`agent/25-*` … `agent/30-*`);
- fixture ownership under `benchmarks/rlh/`;
- stale loop-eval jobs;
- duplicate depth-ablation experiments.

### Per-trace checks (automated when infra exists)

For each new journaled `LoopTrace`:

1. schema valid, hashes present;
2. `ENCODE_CHECK` first, `HALT` + `JOURNAL` last;
3. `encoder_memory_hash` matches the frozen snapshot at `as_of`;
4. no tool response with `known_at > as_of`;
5. no `confidence_source` outside the enum;
6. no numeric probability not copied from `ForecastPackage`;
7. parent timeframe slices unchanged by 5m-only steps;
8. halt reason legal;
9. sample exact-replay canary.

Failures go to `artifacts/watcher/recursive-health.json` and, if blocking, freeze harness promotion.

### Per-completion review (human or Agent 00)

When an RLH agent files a completion report:

1. Read the task contract. Diff must stay in allowed scope.
2. Reject Constitution edits or benchmark deletions.
3. Run `python3 tests/contracts/test_recursive_schemas.py` and the fixture subset named in the contract.
4. Confirm docs updated if schemas moved.
5. Compare process metrics and depth table, not vibes.
6. Approve, reject, quarantine, or reprompt.

## Reprompt template (RLH)

```md
Watcher correction
Agent: <nn>
Task: <task>
Status: REJECTED / NEEDS REVISION
Subsystem: Recursive Learning Harness

Observed failure:
<trace id, fixture id, invariant, hash mismatch, or metric>

Required correction:
<specific LoopStep / halt / memory-bank behavior>

Do not change:
- CONSTITUTION.md
- forecast numeric targets
- September 2026 fixture labels
- unrelated UI or FreqAI adapters

Re-run:
- python3 tests/contracts/test_recursive_schemas.py
- <named RLH fixtures>
- exact replay hash check

Acceptance:
<binary invariant>
```

Prefer a narrower retry over a new architecture.

## Operator kill switch

The UI kill switch is an emergency stop the operator can fire without waiting for Watcher review. It must:

- persist in `artifacts/watcher/kill-switch.json`;
- mark roster tasks `severed`;
- freeze promotion;
- refuse new `LoopStep` / `/api/v1/loops/run` work;
- leave journals immutable.

The current repository implementation is cooperative: it updates the registry/health state and rejects new loop execution. Every agent and connected orchestrator must poll or receive this state and stop. Until an external runtime termination adapter exists, do not claim the API forcibly killed that external process.

Watcher treats an engaged switch as `watcher_abort` for any in-flight loop. Reset is logged; it is not a silent unmute.

## Emergency stop

Freeze RLH promotion and surface `loops/health` red when:

- exact replay mismatch rate > 0 on canaries;
- journal write of `LoopTrace` fails;
- encoder memory missing at loop start;
- NaN/inf in any copied forecast field;
- a loop emits an uncalibrated percentage;
- a loop moves an invalidation;
- real execution code appears in harness tools;
- 5m steps mutate parent encoder slices.

The Forecast Engine may continue if it is healthy. UI must mark explanations `harness-degraded`.

## Artifacts

```text
artifacts/watcher/recursive-health.json
artifacts/watcher/recursive-replays.json
artifacts/watcher/recursive-promotions.json
artifacts/recursive/depth-ablations/
artifacts/recursive/loop-traces/          # optional export; journal is source of truth
```

Do not hand-edit these.

## Competition mode

For uncertain RLH questions, assign 2-5 isolated agents the same fixture set:

- halt threshold (`max_depth` 4 vs 8 vs adaptive);
- whether warm-start helps or harms parent-regime discipline;
- challenge-first vs synthesize-first (synthesize-first must still challenge before halt);
- analog-conditioned explanations.

Competitors must not read each other's `D_φ` until evaluation. Winner is chosen on the same `Recursive-Evaluation.md` gates.

## Living-project cadence

```text
every 5m:  commit ForecastPackage; append LoopTrace before explanation
every matured horizon: append LoopOutcome
hourly:    replay canary + health
daily:     dogfood review of worst process failures
weekly:    depth-ablation + evidence report → new bounded tasks
```

Watcher turns the weekly report into contracts. It does not "turn the loop up to 64" because a tweet said infinite depth.
