# Task contract: Honest market slice

```md
Task: Replace fake-live UI with a Constitution-safe vertical slice: real-or-fixture candles, ContextEngine snapshot, journaled baseline forecast, walk-forward metrics with sample counts, and September 2026 4H-stability replay.
Agent: 17/26/04 (single writer on this branch)
Branch: cursor/honest-market-slice-ee66
Priority: P0

Why:
The UI claimed DATA LIVE and $7.26 on sine-wave candles. Baselines were in-sample. 5m bounce vs 4H bear was unspecified in code.

Allowed write scope:
- packages/context_engine/**
- packages/models/**
- packages/evaluator/**
- packages/journal/**
- packages/fixtures/**
- packages/harness/kill_switch.py
- services/api/**
- apps/web/**
- tests/**
- wiki/Agent-Roster.md
- wiki/Build-Roadmap.md
- apps/web/package.json

Forbidden:
- CONSTITUTION.md
- inventing calibrated probabilities
- enabling trade execution

Acceptance:
- UI never says LIVE unless last close is fresh
- forecast emit uses only candles with close <= as_of
- walk-forward metrics include sample_count and metric name
- zero-model direction is not counted as up
- 5m bounce fixture does not flip 4H regime
- kill switch still blocks /loops/run
```
