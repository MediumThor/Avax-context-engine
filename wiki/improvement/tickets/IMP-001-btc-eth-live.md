# IMP-001 — live BTC/ETH beside AVAX

Residual: AVAX forecasts have almost no real cross-market state. A leveraged operator cannot see sync vs decouple.

Hypothesis: adding leakage-safe BTC/ETH regime and rolling beta, available at `as_of`, improves walk-forward signed direction or MAE versus AVAX-only drift20 on predeclared windows.

Write scope: data ingest, Context Engine `cross_market`, features, evaluator slice `btc_aligned` / `avax_decoupled`.

Forbidden: CONSTITUTION.md; execution; fake probabilities.

Depends on gaps: GAP-BTC-ETH-LIVE (no AccessRequest if Binance Vision/public klines suffice).

Metrics gate (freeze before scoring the challenger):

- target AVAXUSDT 5m h=1..10
- validation walk_forward
- primary: drift20-beating MAE **or** signed_direction on decided samples, with n reported
- must not flip September 2026 4H bear on the 5m bounce
- leverage_sim optional on this ticket

Status: proposed (implementation is a later branch).
