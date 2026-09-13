# WAVE2-35 — Benchmark registry

```md
Task: Create a versioned benchmark registry so later model/context work cannot silently redefine evaluation gates.
Agent: 35
Watcher: 00
Branch: cursor/wave2-35-benchmark-registry-6d82
Priority: P1
Source main commit: b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7
Dependency gate: G5 Evaluation (definitions only; no scored runs)
Review mode: strict-schema

Why:
Promotion and regression gates must be named before candidates are judged. Without a versioned registry, later work can swap metrics, windows, or baselines after seeing results.

Inputs:
- CONSTITUTION.md (§5 leakage, §6 baselines, §13 evidence-gated promotion, §18 September 2026 regression)
- wiki/Home.md
- wiki/Simulation-Accuracy.md
- wiki/Testing-Directive.md
- wiki/Continuous-Improvement-Directive.md
- benchmarks/rlh/README.md (read-only)
- benchmarks/rlh/avax-2026-09-failed-8/ (read-only pointer target)

Allowed write scope:
- benchmarks/registry/**
- wiki/tasks/WAVE2-35-registry.md

Forbidden write scope:
- benchmarks/rlh/**
- CONSTITUTION.md
- packages/**
- services/**
- apps/**
- tests/**
- existing tests (no weaken/delete)

Assumptions:
- No frozen data manifest or sealed walk-forward window exists yet for the core AVAX 5m next-10 task. The draft names the task; it does not invent a dataset window or scores.
- The September 2026 failed ~$8 case already exists as an RLH fixture stub. This task only points at it.
- This registry is the evaluation-gate catalog. LearningCandidate / PromotionDecision machine schemas remain later Agent 35 work and are out of this write scope.

Implementation requirements:
1. README explaining how to add an entry and that promotion requires Watcher + out-of-sample evidence.
2. JSON schema for a registry entry (id, title, dataset_id, time_range, timeframe, metrics, baseline_ids, leakage_rules, status, owner_agent).
3. DRAFT entry for AVAX 5m next-10-candle forecast. Metric NAMES only. Chronological walk-forward only.
4. DRAFT pointer to benchmarks/rlh/avax-2026-09-failed-8/ without modifying that tree. No fabricated outcomes.
5. Stdlib validator under benchmarks/registry/ plus collectable tests in that folder only.

Acceptance tests:
- command: python3 benchmarks/registry/validate.py
  expected: both draft entries validate; no numeric scores present
- command: python3 -m pytest benchmarks/registry/test_benchmark_registry.py
  expected: pass
- command: git diff --name-only
  expected: only benchmarks/registry/** and this task file

Metrics gate:
- baseline: no registry
- required result: draft definitions exist; no accuracy, ECE, coverage, or other numeric performance claims

Historical regressions:
- September 2026 AVAX failed-breakout remains the founding process regression; this task must not rewrite its fixture or invent outcomes

Recursive-learning evidence:
- learning candidate: none
- evaluation plan: none (this task creates draft gate definitions only)
- known failed approaches: none

Docs to update:
- wiki/tasks/WAVE2-35-registry.md (this contract)
- benchmarks/registry/README.md

Finish criteria:
Registry schema + two draft entries + validator exist on the branch. No scores invented. RLH fixture tree untouched. Watcher can open the PR.
```

Watcher owner: Agent 00
Review mode: strict-schema
Competing task group: none
Integration dependency: none
Target main gate: `python3 benchmarks/registry/validate.py` and `python3 -m pytest benchmarks/registry/test_benchmark_registry.py`
