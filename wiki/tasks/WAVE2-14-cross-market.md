# WAVE2-14 — BTC/ETH/AVAX cross-market context

```md
Task: Build BTC/ETH/AVAX relative-strength, rolling correlation/beta, and synchronized/decoupled move flags.
Agent: 14
Branch: cursor/wave2-14-cross-market-19ff
Base: latest main (b6bbbf4)
Priority: P1

Why:
Constitution truth hierarchy places cross-market context (especially BTC and ETH) above quantitative model output. Context Engine v1 must store rolling beta/correlation, relative-strength returns, BTC volatility expansion, and synchronized/decoupled move flags on timestamp-aligned observations only. A missing candle is unknown, not a license to invent or forward-fill.

Inputs:
- CONSTITUTION.md (§2 truth hierarchy, §5 no leakage, §17 no execution)
- wiki/Context-Engine-Directive.md (Cross-market context)
- wiki/Data-Contracts.md (Candle, MarketStateSnapshot.cross_market)
- wiki/Market-State-Spec.md (unknown state; relative-strength decoupling)
- wiki/Testing-Directive.md (future-candle leakage; gap handling)
- wiki/Documentation-Standards.md (symbols AVAXUSDT/BTCUSDT/ETHUSDT/AVAXBTC)
- packages/context_engine/models.py (Candle; read-only)
- packages/context_engine/indicators.py (read-only; not used across gaps)

Allowed write scope:
- packages/context_engine/cross_market.py
- tests/test_cross_market.py
- wiki/tasks/WAVE2-14-cross-market.md

Forbidden write scope:
- CONSTITUTION.md
- packages/context_engine/engine.py
- services/harness/**
- apps/web/**
- packages/market_data/store.py
- packages/features/** (Agent 03)
- real trade execution

Dependencies:
- Candle timezone-aware OHLC contract
- No overlap with WAVE2-03 feature assembler or PR 8 engine/API/UI files
- Shared MarketStateSnapshot.cross_market schema remains Agent 31; this module emits a typed snapshot dict for later wiring

Implementation requirements:
1. Align timestamps exactly. If a series is missing a candle at the evaluation timestamp or at the immediately prior bar, mark that 1-bar feature unknown rather than invent, interpolate, or use the last available print.
2. Features at T use only closes known at T: closed candles with open_time <= T. Unclosed and future bars are ignored.
3. Rolling correlation/beta require every expected timestamp in the lookback window on both legs. A gap makes those window statistics unknown; they must not be computed on a compacted intersection.
4. Tests: gap handling; a future BTC candle cannot change the AVAX/BTC feature at T.
5. No trade execution. No orders, brokers, or position sizing.
6. Expose relative-strength (log-return difference), Pearson correlation, OLS beta, BTC volatility regime, and synchronized breakout/breakdown vs decoupled flags.

Acceptance tests:
- command: python -m pytest -q tests/test_cross_market.py
  expected: all tests pass
- missing aligned candle => unknown, not a filled value
- mutating BTC after T does not change CrossMarketState at T
- unclosed BTC bar at T is ignored

Metrics gate:
- baseline: no cross-market module
- required result: deterministic state + leakage/gap tests; no forecast accuracy claim

Historical regressions:
- none owned in this increment (September 2026 fixture remains context/data agents)

Docs to update:
- wiki/tasks/WAVE2-14-cross-market.md (this contract)

Finish criteria:
cross_market.py + test_cross_market.py + this contract exist; pytest tests/test_cross_market.py is green; gaps are unknown; future BTC cannot leak into T; no execution code.
```

Watcher owner: Agent 00
Review mode: strict-quant
Competing task group: none
Integration dependency: Agent 16 snapshot wiring; Agent 31 cross_market schema
