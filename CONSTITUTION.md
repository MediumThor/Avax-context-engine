# AVAX Context Engine Constitution

**Status: IMMUTABLE PROJECT LAW**

This document is the highest-authority instruction set for every human, AI agent, watcher, subagent, script, benchmark, and automated improvement loop operating in this repository. Agents may not edit, reinterpret, bypass, weaken, or supersede it. If implementation conflicts with this document, implementation is wrong.

## 1. Mission

Build a living market-context and forecasting system that continuously ingests AVAX and correlated-market data, maintains persistent multi-timeframe context, produces calibrated probabilistic forecasts for the next 10 five-minute candles, measures every forecast against realized outcomes, and improves only when out-of-sample evidence shows an improvement.

The system is a research and decision-support instrument. It does not execute trades in v1. Execution remains external.

## 2. Core truth hierarchy

The system MUST reason in this order:

1. Data integrity and timestamp correctness.
2. Higher-timeframe market regime.
3. Confirmed market structure and structural invalidation.
4. Cross-market context, especially BTC and ETH.
5. Quantitative model output and uncertainty.
6. Lower-timeframe execution context.
7. Narrative explanation.

A lower layer may refine a higher layer but may not silently overwrite it. A 5m squeeze does not invalidate a bearish 4H regime. A narrative does not override measured data.

## 3. No moving goalposts

Every active thesis MUST include explicit confirmation and invalidation conditions before subsequent candles arrive. Once an invalidation condition is met, the thesis is closed or changed. Agents may not retroactively move invalidation levels to preserve a prior thesis.

## 4. No fake certainty

Forecasts are distributions, not prophecies. The system MUST report uncertainty, calibration and historical performance. Subjective confidence percentages without a defined calibration source are prohibited in production output.

## 5. No leakage

No feature, model, simulation, label, resampling operation, higher-timeframe aggregation or context snapshot may contain information unavailable at the forecast timestamp. Random time-series train/test splitting is prohibited for accuracy claims. Walk-forward or equivalent chronology-preserving validation is mandatory.

## 6. Baselines before sophistication

Every new model MUST be compared against simple baselines: zero return, persistence/drift, EMA/trend heuristic and a simple statistical classifier/regressor. A complex model is not an improvement unless it beats appropriate baselines out of sample after fees/slippage assumptions where relevant.

## 7. Prediction journal is append-only

Every live or simulated forecast MUST be written before outcomes are known. Forecast records include model version, feature/schema version, context snapshot ID, source data hashes, horizons 1-10, probability/quantile outputs and timestamp. Outcomes are appended later. Historical predictions may never be overwritten to improve apparent accuracy.

## 8. Context is persistent

The Context Engine MUST maintain a versioned state graph across weekly, daily, 4H, 1H, 15m and 5m timeframes. New candles update state; they do not erase history. Every state transition must be explainable from observable events.

## 9. Real structure over decoration

Support/resistance, trendlines, Fibonacci anchors, Elliott hypotheses and chart annotations must be derived from reproducible rules or explicitly tagged as analyst annotations. User-drawn lines have no inherent authority. A level is not promoted to structural support solely because it appears on a chart.

## 10. Pattern hypotheses are competing hypotheses

Elliott Wave, Wyckoff, breakout/retest, accumulation/distribution, volatility compression and other pattern frameworks may be represented, but no pattern framework is privileged. Pattern candidates carry evidence, counter-evidence, confidence provenance and invalidation.

## 11. Freqtrade/FreqAI is infrastructure, not the brain

Freqtrade/FreqAI provides proven data, feature, training, backtesting and research infrastructure. The custom Context Engine and Internal AI Harness remain first-class modules with their own contracts. Upstream code must be pinned and license boundaries documented. Do not fork upstream casually when an adapter can preserve upgradeability.

## 12. UI must expose reasoning state

The UI is not merely a candlestick viewer. It must show:

- current regime by timeframe;
- validated structural zones and provenance;
- active bull/bear hypotheses and invalidations;
- next-10-candle probabilistic forecast bands;
- model agreement/disagreement;
- recent forecast accuracy and calibration;
- data freshness and health;
- an audit trail of state changes.

## 13. Continuous improvement is evidence-gated

Automated agents may propose, implement and test improvements continuously. No change is promoted because it sounds smarter, increases in-sample fit, or produces one attractive backtest. Promotion requires predefined evaluation gates and watcher approval.

## 14. Agent concurrency rules

Up to 40 subagents may work concurrently, but they must use isolated branches/worktrees or otherwise non-overlapping write scopes. Every agent must have a task contract, owner, inputs, outputs, forbidden areas, tests and completion criteria. Agent 00 is the Watcher and has review authority over all other agents.

## 15. Watcher authority

The Watcher continuously checks:

- Constitution compliance;
- task overlap and conflicting edits;
- data leakage;
- test failures;
- undocumented schema changes;
- regression in out-of-sample metrics;
- stale branches;
- incomplete documentation;
- false accuracy claims.

The Watcher may reject work, reopen tasks, reprompt an agent with a narrower contract, or quarantine an experiment. It may not weaken this Constitution.

## 16. Reproducibility

Every claimed result must be reproducible from a commit SHA, config, data manifest and deterministic seed where feasible. If data is external or mutable, snapshot identifiers and checksums are required.

## 17. Safe operability

No production UI or agent may place a real trade unless the Constitution is explicitly amended by the repository owner in a separate human-governed process. v1 is read-only market analysis and simulation.

## 18. Dogfooding

The project must be used against real incoming market data. Every defect discovered through use becomes a documented issue, regression test or benchmark case. The September 2026 AVAX ~$8 failed-breakout episode is a permanent regression case for context drift and moving-goalpost behavior.

## 19. Documentation is executable context

Architecture, schemas, agent directives, benchmark definitions and operational procedures must stay versioned with code. Agents must read the relevant wiki pages before modifying a subsystem and must update documentation when contracts change.

## 20. Definition of success

Success is not "predict every candle." Success is a system that is measurably better calibrated and more useful than simple baselines, detects when it does not know, preserves higher-timeframe context, learns from every forecast, and improves without rewriting history.
