# WAVE2-13 — Competing pattern hypotheses

```md
Task: Implement pattern hypotheses as competing scored objects with evidence, counter-evidence, confirmation, and immutable invalidation.
Agent: 13
Branch: cursor/wave2-13-patterns-ee82
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G3 (Context Engine pattern layer)

Watcher owner: Agent 00
Review mode: strict-schema
Competing task group: none
Integration dependency: none
Target main gate: python -m pytest -q tests/test_patterns.py tests/test_context_engine.py tests/test_leakage.py

Why:
Constitution §10 requires pattern frameworks to be competing hypotheses, not privileged labels. Constitution §3 forbids moving invalidation after create time. Constitution §5 forbids using pivots or candles that were not knowable at T. A 5m relief bounce must not confirm a 4H continuation. Elliott counts, if emitted, stay labeled candidates and never outrank other patterns by name.

Inputs:
- CONSTITUTION.md (§3, §5, §9, §10)
- wiki/Home.md
- wiki/Context-Engine-Directive.md (pattern hypotheses, Elliott handling, timeframe hierarchy)
- wiki/Testing-Directive.md (leakage, pivot known_at, parent/child)
- wiki/Data-Contracts.md (Hypothesis target fields; this module does not own the shared schema)
- wiki/Market-State-Spec.md (failed breakout vs reclaim; 5m relief is not a higher-TF reversal)
- packages/context_engine/models.py (Candle, Pivot) — read only
- packages/context_engine/structure.py (confirmed_pivots) — read only, do not rewrite

Allowed write scope:
- packages/context_engine/patterns.py
- tests/test_patterns.py
- wiki/tasks/WAVE2-13-patterns.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- packages/context_engine/zones.py
- packages/context_engine/fibonacci.py
- packages/context_engine/thesis.py
- packages/context_engine/cross_market.py
- packages/context_engine/replay.py
- packages/context_engine/pivots_atr.py
- packages/contracts/recursive/**
- services/harness/**
- apps/web/**
- real trade execution
- claiming a pattern is confirmed structure or a trade signal
- fabricated confidence percentages

Dependencies:
- Candle / Pivot types and confirmed_pivots on main @ b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
- No shared-schema write; Agent 15 owns thesis ledger; this module stays self-contained

Assumptions:
- A candle is usable at T only when is_closed is true and period_end <= T.
- A pivot is usable at T only when known_at <= T.
- Invalidation rules are frozen on the hypothesis version that created them.
- evidence_score is an uncalibrated count-derived rank, not a calibrated confidence percentage.
- Pattern status stays candidate or active until same-timeframe confirmation rules fire.
- Elliott hypotheses remain status=candidate and privileged=False.

Implementation requirements:
1. Import Pivot/Candle; call confirmed_pivots; do not rewrite structure.py.
2. Emit competing hypotheses: continuation, flag, wedge/triangle, compression, failed_breakout, successful_reclaim, accumulation/distribution; optional Elliott impulse/correction as labeled candidates.
3. Every hypothesis carries evidence, counter_evidence, confirmation (fired items), confirmation_rules, and immutable invalidation rules.
4. Moving invalidation on an existing version raises ImmutableInvalidationError (Constitution §3).
5. Failed-breakout and successful-reclaim are distinct outcomes and never collapse into each other.
6. Deterministic scoring from evidence / counter-evidence / confirmation counts only. No LLM. No confidence field.
7. Timezone-aware UTC only.
8. 5m observations cannot fire 4H confirmation or invalidation rules.

Acceptance tests:
- command: python -m pytest -q tests/test_patterns.py tests/test_context_engine.py tests/test_leakage.py
  expected: all tests pass
- unfinished / future pivots cannot create or confirm a hypothesis at T
- perturb candles after T; hypotheses at T unchanged
- invalidation cannot be moved
- 5m relief does not confirm a 4H continuation
- no pattern name is treated as unconditional truth (status stays candidate/active until confirmation rules fire)

Metrics gate:
- baseline: no pattern-hypothesis module on main
- required result: deterministic hypotheses + leakage/immutability tests; no forecast accuracy claim

Historical regressions:
- September 2026 spirit: failed-breakout and successful-reclaim remain distinct; a later 5m bounce does not rewrite or confirm a higher-timeframe pattern

Docs to update:
- wiki/tasks/WAVE2-13-patterns.md (this contract)

Finish criteria:
patterns.py + test_patterns.py + this contract exist on the branch; required pytest suites are green; no CONSTITUTION.md edit; no accuracy or confidence-percentage claims; Watcher (Agent 00) opens any PR.
```
