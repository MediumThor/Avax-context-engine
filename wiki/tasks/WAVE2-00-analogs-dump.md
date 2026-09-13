# WAVE2-00 — Snapshot analogs + sealed September dump

```md
Task: Attach leakage-safe analog matches and pattern/fib summaries to Context Engine snapshots, and seal the September 2026 fixture as candles.jsonl.
Agent: 00
Branch: cursor/engine-analogs-dump-8771
Priority: P0
Source main commit: 12f9be4
Dependency gate: G3 Context

Why:
DoD requires multi-timeframe structure, analog context, and a permanent September 2026 dump. engine.build_snapshot previously only did EMA/pivot clusters.

Scope:
- packages/context_engine/analogs.py (new)
- packages/context_engine/engine.py
- packages/context_engine/models.py (additive snapshot fields)
- scripts/export_sept_fixture.py
- benchmarks/rlh/avax-2026-09-failed-8/candles.jsonl + manifest.json
- tests/test_engine_analogs.py, tests/test_sept_dump.py
- apps/web rail types + analog/pattern/fib display (not confidence)
- wiki: Context-Engine-Directive, Market-State-Spec, Data-Contracts, Build-Roadmap, this contract

Assumptions:
- Analog candidates are origins whose h=10 close is already known at T.
- Fingerprint uses only the prefix visible at each origin.
- Realized h=10 is attached only because that close is <= T. It is not a forecast and not a calibrated confidence score.
- Pattern evidence_score stays score_provenance=evidence_count_v1.
- Fibonacci levels stay candidate context features, never guaranteed support.
- Sealed dump is the fixture generator output plus sha256; it does not invent live prints.

Forbidden:
- CONSTITUTION.md
- packages/contracts/recursive/**
- packages/models/baselines.py
- fabricated analog confidence / accuracy
- using analog outcomes whose h=10 close is after T
- promoting quantiles or claiming FreqAI beats drift20

Tests:
- retrieve_analogs ignores post-T candles
- snapshot.to_dict() includes analogs/pattern_hypotheses/fib_levels
- WAVE-2 future perturbation still holds on full to_dict()
- sealed dump sha256 + candle_count match manifest and the fixture generator
- fixture /market payload exposes analogs without a confidence field

Finish:
- dump status=sealed with checksum
- snapshot fields wired and leakage-safe
- UI shows historical analogs as known-at-T context
- tests pass; no fabricated confidence
```
