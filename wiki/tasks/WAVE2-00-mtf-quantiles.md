# WAVE2-00 — Quantile challenger trains on avax.features.mtf.v1

```md
Task: Replace the placeholder quantile feature schema with leakage-safe avax.features.mtf.v1 rows and a drift20-centered ridge residual fallback.
Agent: 00
Branch: cursor/mtf-quantile-features-8771
Priority: P0
Source main commit: 80a4d7035046dc7c59f4f4442d5298d40ce0a929
Dependency gate: G4/G5 (challenger still not promoted)

Why:
PR 30 journals MTF snapshots but the model still trains on freqai.quantiles.features.v1. Walk-forward on the September fixture showed last-bar residual quantiles lose to drift20. The model must consume the same features it journals.

Inputs:
- packages/features (avax.features.mtf.v1)
- packages/models/freqai_quantiles.py
- services/api/runtime.py
- wiki/ML-FreqAI-Directive.md

Allowed write scope:
- packages/models/freqai_quantiles.py
- services/api/runtime.py
- tests/test_mtf_quantile_features.py
- tests/test_freqai_quantiles.py (schema assertions only if required)
- wiki/tasks/WAVE2-00-mtf-quantiles.md
- wiki/Build-Roadmap.md

Forbidden write scope:
- CONSTITUTION.md
- packages/models/baselines.py
- packages/contracts/recursive/**
- fabricated ECE / promotion

Implementation requirements:
1. Train/predict using assemble_features at each eligible origin (period_end <= T).
2. Python fallback: ridge on residual vs drift20*h, then empirical leftover quantiles. No shuffle.
3. Live runtime passes BTC candles known at T.
4. feature_schema_version on the quantile payload is avax.features.mtf.v1.
5. Re-score or keep walk-forward helper unchanged; do not set freqai_beats_baselines.

Acceptance tests:
- python3 -m pytest -q tests/test_mtf_quantile_features.py tests/test_freqai_quantiles.py tests/test_live_quantile_journal.py
- future AVAX/BTC perturbation after T does not change the forecast at T
- q10 <= q50 <= q90
```

## Status

Implemented on `cursor/mtf-quantile-features-8771` from `origin/main` `80a4d70`.

Python fallback is `mtf_ridge_residual_quantiles.v1`: q50 = drift20·h + ridge(MTF residual); q10/q90 width is the empirical residual vs drift20 (not in-sample leftover after ridge). Live runtime passes BTC known at T. Payload `feature_schema_version` is `avax.features.mtf.v1`.

Not a promotion. `freqai_beats_baselines` remains null.
