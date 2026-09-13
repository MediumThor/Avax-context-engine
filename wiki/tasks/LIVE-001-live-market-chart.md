# Task contract: Live AVAX chart (not fixture)

```md
Task: Default the operator workspace to live Binance Vision AVAXUSDT candles and last trade, with incremental refresh. Fixture data is explicit/offline only.
Agent: 01/17/31 (this cloud agent)
Branch: cursor/live-avax-chart-86f1
Base: origin/main @ 12f9be4d4140255d7369afec8b5532df58459a4b
Priority: P0
Kill switch: not engaged

Why:
The workspace showed the September 2026 failed-breakout fixture (~$7.58 synthetic path) while live AVAX was ~$7.31. `_ensure` never refreshed after the first fill and silently seeded the fixture when a live pull failed.

Allowed write scope:
- packages/market_data/binance.py
- services/api/runtime.py
- services/api/main.py
- apps/web/src/App.tsx
- apps/web/src/api/market.ts
- apps/web/src/api/types.ts
- apps/web/src/components/MarketChart.tsx
- tests/test_live_market.py
- tests/test_market_data.py
- wiki/tasks/LIVE-001-live-market-chart.md
- wiki/Build-Roadmap.md
- wiki/Agent-Build-Plan.md
- README.md
- .env.example
- .gitignore
- .cursor/plans/live-market-chart.md

Forbidden:
- CONSTITUTION.md
- packages/contracts/recursive/**
- enabling trade execution
- silently labeling fixture or stale bars LIVE
- using an unfinished 5m bar as a closed candle in features/forecasts
- rewriting quantile / walk-forward scoring logic

Assumptions:
- Public `data-api.binance.vision` klines + ticker/price are the live source.
- Ticker last price may update the header; the chart and forecasts use closed 5m candles only.
- `AVAX_USE_FIXTURE=1` remains the September 2026 process-check / offline path.

Dependencies:
- Existing CandleStore immutability
- Existing freshness() 12-minute LIVE gate
- Kill switch not engaged

Tests:
- pytest tests/test_live_market.py tests/test_honest_slice.py tests/test_market_data.py
- live pull failure with empty store must 503 and must not flip to fixture
- stale store must append newly pulled closed candles
- fixture mode still returns health=fixture

Finish criteria:
- Default `/api/v1/market/AVAXUSDT` source is `binance-vision`
- Header last_price tracks ticker when reachable (currently ~7.31)
- Chart candles are real closed 5m OHLC, refreshed on poll
- Screenshot of LIVE workspace, not FIXTURE
```
