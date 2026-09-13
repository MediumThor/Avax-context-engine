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

## Status

Implemented on `cursor/wave2-14-cross-market-19ff` from latest `main` (`b6bbbf4`). Tests green.

## Completion report

### What changed

Leakage-safe BTC/ETH/AVAX cross-market context module. Evaluation at T uses only closed candles with `open_time <= T`. Series are aligned on exact `open_time`. A missing candle is `unknown`; the module does not interpolate, forward-fill, or compact a gapped window into consecutive returns.

Emits:

- 1-bar and window relative strength (focal log return minus reference log return) for AVAX/BTC, AVAX/ETH, ETH/BTC
- Pearson correlation and OLS beta over a consecutive lookback (default 24; tests use 8)
- synchronized breakout / synchronized breakdown / decoupled / quiet flags
- BTC return-sign regime and gap-aware realized-vol expansion/compression
- optional native `AVAXBTC` 1-bar log return when that series is aligned

Schema version: `avax.cross_market.v1`. No trade execution. `engine.py` is unchanged; Agent 16 can wire `CrossMarketState.to_dict()` into `MarketStateSnapshot.cross_market`.

### Exact files changed

- `packages/context_engine/cross_market.py`
- `tests/test_cross_market.py`
- `wiki/tasks/WAVE2-14-cross-market.md`

### Tests run

```
python3 -m pytest -q tests/test_cross_market.py
python3 -m pytest -q tests/test_context_engine.py tests/test_leakage.py tests/test_cross_market.py
```

- `tests/test_cross_market.py`: **14 passed**
- with existing context/leakage: **18 passed**

Covered: exact-alignment RS; missing BTC at T is unknown (not last-print fill); gap in window makes corr/beta unknown (not compacted intersection); future BTC/AVAX mutation does not change state at T; unclosed BTC bar ignored; ETH absent degrades overall health; native AVAXBTC alignment; naive `as_of` rejected.

### Metrics before/after

Not applicable. No model training, no accuracy claims, no walk-forward scores.

### Known limitations

- Not wired into `ContextEngine.build_snapshot` (engine.py is out of scope).
- `btc_regime` is a window log-return heuristic, not Agent 09's multi-timeframe BTC regime machine.
- Rolling corr/beta require a complete exact grid of `window+1` stamps; short history is `degraded`, not estimated.
- Window relative strength uses endpoints only; corr/beta require every intermediate stamp.
- Shared `MarketStateSnapshot.cross_market` OpenAPI/Pydantic contract remains Agent 31.

### Documentation updated

- `wiki/tasks/WAVE2-14-cross-market.md` (contract + this report)

### Contract/schema change

Additive only: `avax.cross_market.v1` snapshot dict. Does not mutate RLH JSON schemas or `engine.py` snapshot shape.

### Recommended next task

Agent 16: attach `build_cross_market(...).to_dict()` to versioned snapshots/fingerprints with the same `as_of` cutoff. Agent 31: freeze the `cross_market` object in the canonical MarketStateSnapshot schema. Agent 09: replace the BTC return-sign heuristic with the accepted BTC timeframe regime when that module lands.

