# WAVE2-00 — Walk-forward Brier / ECE / coverage

```md
Task: Score the live empirical P(up) and residual interval on chronological walk-forward origins and expose those scores in /market + AccuracyPanel. Score journaled matured rows when n is sufficient.
Agent: 00
Branch: cursor/journal-cal-scores-8771
Priority: P0
Source main commit: a30d197
Dependency gate: G5 Evaluation

Why:
AccuracyPanel currently hard-codes Brier/ECE/coverage as null. Constitution §4 requires reported calibration. The live path already emits empirical_signed_base_rate.v1.

Forbidden:
- CONSTITUTION.md
- packages/models/baselines.py
- fabricated confidence / promoting FreqAI
- shuffle validation
- using candles after as_of
```
