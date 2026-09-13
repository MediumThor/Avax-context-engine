# WAVE2-37 — Journal and snapshot replay red team

```md
Task: Red-team journal + snapshot replay for leakage and journal-before-outcome
Agent: 37
Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: none
Integration dependency: none (read-only on packages/**)
Branch: cursor/wave2-37-replay-redteam-29ee
Base: latest origin/main (b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7 at branch cut)
Isolation: temporary branch cursor/wave2-37-replay-redteam-29ee
Integration target: main
Priority: P0
Dependency gate: G3/G4 journal + context snapshot (QA only)

Why:
Constitution §§2, 5, 7 require that a forecast/journal record written at T is
frozen before outcomes exist, that later candles cannot rewrite it, and that a
5m bounce cannot silently overwrite a higher-timeframe regime already journaled
at T. Independent QA must prove those invariants against the APIs that exist on
main, without editing production code.

Inputs:
- CONSTITUTION.md (immutable; §§2 hierarchy, §5 no leakage, §7 append-only journal)
- wiki/Home.md
- wiki/Testing-Directive.md (leakage + journal immutability + replay determinism)
- wiki/Simulation-Accuracy.md (walk-forward / no-hindsight scoring)
- wiki/Prediction-Journal.md
- wiki/Context-Engine-Directive.md
- wiki/Data-Contracts.md (ForecastPackage vs ForecastOutcome)
- packages/journal/journal.py (read-only)
- packages/context_engine/engine.py (read-only)
- tests/test_leakage.py, tests/test_journal.py (read-only)
- origin/cursor/wave2-16-replay-d941 packages/context_engine/replay.py (ideas only;
  not a runtime dependency unless that module is already on main)

Allowed write scope:
- tests/replay/**
- wiki/tasks/WAVE2-37-replay-redteam.md

Forbidden write scope:
- CONSTITUTION.md
- packages/**
- services/**
- apps/**
- tests/test_leakage.py
- tests/test_journal.py
- tests/test_replay.py
- tests/replay/test_replay.py
- tests/replay/test_leakage.py
- weakening or deleting existing tests

Assumptions:
- Current main has no packages.context_engine.replay. Required probes MUST run
  against ContextEngine.build_snapshot + ForecastJournal. Optional replay-module
  probes MAY skip (not fail) with an explicit reason when that module is absent.
- ContextEngine.build_snapshot treats as_of as the last closed 5m open_time in
  the list the caller passes. Tests that speak of “at T” therefore pass only
  candles knowable at T, matching tests/test_leakage.py.
- resample_closed on main emits a parent bar only when the 5m bucket is full.
  Unfinished (is_closed=False) 5m bars and incomplete parent buckets must not
  change higher-timeframe evidence.
- ForecastJournal stores forecast rows separately from outcome rows. A forecast
  payload written at T must not contain ForecastOutcome fields.
- Pytest collects by basename. This task must not create test_replay.py or
  test_leakage.py anywhere.
- No forecast accuracy is claimed. Horizon numbers in fixtures are structural
  placeholders, not calibrated probabilities.
- No real trade execution.

Implementation requirements:
1. Unique test module name tests/replay/test_journal_replay_redteam.py.
2. Prove the journal record at T is byte-stable (payload + sha256) after later
   candles are mutated.
3. Prove a forecast written at T has no outcome/realized fields, and that
   append_outcome later does not mutate the forecast row.
4. Prove unfinished / incomplete parent candles do not change 1h/4h/1d evidence
   on ContextEngine.build_snapshot (and on replay APIs when present).
5. Prove the same raw 5m series rebuilds the same snapshot (and the same
   journalable payload).
6. Prove a 5m bounce after a 4H bearish parent does not rewrite the journaled
   4H regime at T.
7. If packages.context_engine.replay exists, repeat the as-of probes through
   that API. If it does not, skip those extra probes only.

Acceptance tests:
- command: python -m pytest -q tests/replay tests/test_leakage.py tests/test_journal.py
  expected: required red-team probes collect and run against main APIs; existing
  leakage/journal tests still pass; optional replay-module tests skip only when
  that module is absent.

Metrics gate:
- none (no forecast/accuracy claims; this is an invariance red team)

Historical regressions:
- not the September 2026 fixture in this increment (no extra fixture files);
  4H-parent vs 5m-bounce is the local hierarchy regression.

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-37-replay-redteam.md only (this contract)

Completion report must contain:
- files changed
- tests run and results
- bugs found (if any)
- no accuracy claims
- limitations
- recommended next task
- whether any contract/schema changed

Finish criteria:
- task contract exists
- uniquely named tests exist under tests/replay/
- required probes do not depend on files that are not on main
- branch committed and pushed; no GitHub PR opened (Watcher opens it)
- CONSTITUTION.md and packages/** untouched
```
