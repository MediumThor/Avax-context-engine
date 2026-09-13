# AVAX Context Engine

AVAX Context Engine is a read-only market-context and probabilistic-forecasting system for AVAX. It combines a pinned Freqtrade/FreqAI backbone with a custom deterministic Context Engine, an append-only Prediction Journal, a custom Recursive Learning Harness (RLH), chronology-safe evaluation, and a mobile-first React/TradingView Lightweight Charts Web App.

It is designed to answer three questions without rewriting history:

1. What is the AVAX market state across `1w`, `1d`, `4h`, `1h`, `15m`, and `5m`?
2. What calibrated distribution does the Forecast Engine assign to horizons `h=1..10`?
3. Did the forecast and explanation remain useful, reproducible, and better than appropriate baselines after outcomes matured?

## Current status

`main` contains a working prototype spine: public-data helpers, a Context Engine prototype, baseline/evaluator and journal primitives, FreqAI configuration, FastAPI endpoints, an RLH schema/fixture foundation with an operator kill switch, CI, Docker scaffolding, and a React shell. Several paths are intentionally stubs; the production data contracts, persistent state, complete forecasting/evaluation loop, working recurrent LoopStep, and full mobile operator experience are not finished.

The exact verified baseline and remaining gates live in [`wiki/Agent-Build-Plan.md`](wiki/Agent-Build-Plan.md). Do not infer completion from the presence of a directory.

## Non-negotiable boundaries

- v1 provides research, explanation, replay, and simulation only; it does not execute trades.
- Forecasts are distributions with measured uncertainty, not deterministic price calls.
- Lower-timeframe movement cannot silently rewrite higher-timeframe state.
- A countertrend short in a bullish higher-timeframe regime remains tactical unless explicit reversal criteria trigger.
- Forecasts and RLH LoopTraces are journaled before their outcomes are known.
- More loop depth is not an accuracy claim; model or harness promotion requires predeclared out-of-sample evidence.
- `main` is the only durable product state. Agent isolation surfaces are temporary.

## Product loop

```text
closed market data -> validated observations -> Context Engine snapshot
-> frozen features/EncoderMemory -> ForecastPackage -> bounded RLH LoopTrace
-> atomic journal -> mobile-first Web App -> matured outcomes
-> Evaluation Engine -> evidence-linked improvement candidate -> Watcher -> main
```

## Start here

- [`CONSTITUTION.md`](CONSTITUTION.md) — immutable project law.
- [`AGENTS.md`](AGENTS.md) — current mainline, kill-switch, and agent rules.
- [`wiki/Home.md`](wiki/Home.md) — documentation authority and reading paths.
- [`wiki/Agent-Build-Plan.md`](wiki/Agent-Build-Plan.md) — current baseline, dependency gates, ownership, and complete build order.
- [`wiki/UI-Directive.md`](wiki/UI-Directive.md) — mobile-first product contract.
- [`wiki/Recursive-Learning-Harness.md`](wiki/Recursive-Learning-Harness.md) — per-forecast recurrent reasoning architecture.
- [`wiki/Continuous-Improvement-Directive.md`](wiki/Continuous-Improvement-Directive.md) — evidence-to-code learning and promotion.

Before launching an RLH task, also read [`wiki/Agent-Roster.md`](wiki/Agent-Roster.md), [`wiki/Recursive-Agent-Batch.md`](wiki/Recursive-Agent-Batch.md), and the live kill-switch state.
