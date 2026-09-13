# WAVE2-36 — Independent leakage red team

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: WAVE2-leakage
Integration dependency: none (works against current main; optional WAVE-2 modules skip)
Target main gate: `python -m pytest -q tests/leakage/wave2 tests/test_leakage.py`

```md
Task: Blocking point-in-time leakage probes for Context Engine, structure, journal, and optional WAVE-2 feature assembly.
Agent: 36
Branch: cursor/wave2-36-leakage-redteam-1572
Priority: P0
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G2 chronology / no-leakage (Constitution §5)

Why:
A snapshot, journal row, pivot, or feature that can see T+1 is worse than a dumb baseline. Independent QA must fail the build on future leakage rather than trusting author tests.

Inputs:
- CONSTITUTION.md §5 (no leakage), §2 (parent regime hierarchy)
- wiki/Testing-Directive.md (leakage layer)
- wiki/Data-Contracts.md (unfinished parents, is_closed)
- wiki/Market-State-Spec.md (parent/child; 5m bounce is not a 4H flip)
- tests/test_leakage.py (READ ONLY; do not weaken)
- packages/context_engine on current main (ContextEngine.build_snapshot, resample_closed, confirmed_pivots)
- packages/journal.ForecastJournal
- packages/models.evaluate_baselines
- packages/harness.synthesis.build_analysis

Allowed write scope:
- tests/leakage/wave2/**
- wiki/tasks/WAVE2-36-leakage.md

Forbidden write scope:
- CONSTITUTION.md
- packages/** (do not patch production to silence a probe)
- tests/test_leakage.py
- tests/leakage/rlh/** (Watcher / PR 9)
- random-shuffle validation
- fabricated accuracy claims
- creating tests/leakage/wave2/test_leakage.py, test_replay.py, or test_probes.py (pytest collects by basename)

Assumptions:
- Current main ContextEngine.build_snapshot consumes a 5m series and uses only closed candles; as_of is the last closed 5m open_time unless a later WAVE-2 API adds an explicit as_of.
- resample_closed on main emits a parent bar only when the bucket has the expected number of closed 5m candles.
- confirmed_pivots on main requires `right` confirming bars; known_at is the confirming candle time.
- Optional WAVE-2 feature assembler / replay-as-of modules may be absent; those probes skip, they do not fail.
- Probes import production code; they must not edit it.

Implementation requirements:
1. Mutate candles after T; ContextEngine snapshot at T (or journal payload at T) is unchanged.
2. Unfinished 15m/1h/4h/1d parents do not appear in HTF state at T.
3. A pivot that is not confirmed at T cannot appear in structure used at T (confirmed_pivots on main).
4. Feature/target contamination: use a feature assembler if importable; otherwise assert baseline/journal payloads do not include future close columns for later horizons as features.
5. A 5m bounce does not flip a completed 4H parent regime on the snapshot at T.

Acceptance tests:
- command: python -m pytest -q tests/leakage/wave2 tests/test_leakage.py
  expected: all collected probes pass, or fail only on real leakage. Optional-module cases skip. Existing tests/test_leakage.py still passes.

Metrics gate:
- baseline: none (red team; no accuracy claims)
- required result: no leakage through snapshot/journal/pivots/HTF/targets; no fabricated scores

Historical regressions:
- none added (September 2026 case remains owned elsewhere)

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-36-leakage.md (this contract)

Finish criteria:
Five uniquely named probe modules under tests/leakage/wave2/. tests/test_leakage.py untouched. No packages/** edits. Branch pushed. Watcher opens the PR.
```
