# WAVE2-00 — Journal outcomes + empirical direction probability

```md
Task: Append matured forecast outcomes without rewriting journal rows, and attach a leakage-safe empirical P(close > origin) with an explicit calibration ref.
Agent: 00
Branch: cursor/journal-outcomes-cal-8771
Priority: P0
Source main commit: 0dd60fa
Dependency gate: G4/G5

Why:
The live path journals forecasts but never appends outcomes, so the system cannot learn. p_close_above_origin is always null, so the fan cannot show a probability with a calibration source.

Inputs:
- wiki/Prediction-Journal.md
- packages/journal/journal.py
- packages/evaluator/calibration.py
- packages/models/freqai_quantiles.py

Allowed write scope:
- packages/journal/journal.py
- packages/models/direction_cal.py
- packages/models/outcomes.py
- packages/models/freqai_quantiles.py
- packages/models/__init__.py
- services/api/runtime.py
- tests/test_journal_outcomes.py
- tests/test_live_quantile_journal.py (p assertions)
- tests/test_honest_slice.py (p assertions)
- wiki/tasks/WAVE2-00-outcomes-cal.md
- wiki/Prediction-Journal.md
- wiki/Build-Roadmap.md

Forbidden:
- CONSTITUTION.md
- packages/models/baselines.py
- fabricated ECE as live accuracy
- overwriting forecast payloads

Requirements:
1. When later closed candles exist, append outcomes for prior journal rows. Idempotent. Forecast hash unchanged.
2. Replay/as_of may only mature using candles visible at as_of.
3. Empirical P(up) per horizon from signed drift20 buckets on train origins whose outcomes are known at T. Min count 8. Else null.
4. calibration_ref = empirical_signed_base_rate.v1 when a probability is emitted.
5. No promotion claim.

Acceptance:
- pytest tests/test_journal_outcomes.py tests/test_live_quantile_journal.py tests/test_honest_slice.py
- future candles do not change p or outcomes at T
```
