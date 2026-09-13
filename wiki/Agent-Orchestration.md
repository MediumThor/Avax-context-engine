# Agent Orchestration

## Objective

Operate the repository as a continuously improving multi-agent engineering system without allowing concurrency to degrade correctness.

The project supports up to 40 active agents. Concurrency is useful only when write scopes, contracts and review authority are explicit.

## Agent 00 — Watcher

Agent 00 is always reserved for the Watcher. It does not primarily build features. It observes work, detects conflicts, verifies evidence, reprompts weak agents, and integrates accepted work.

Agent 00 reads every task contract and completion report. It has authority to reject or quarantine work.

## Recommended lanes

### 01-08 Quant and ML

- 01 Data ingestion and integrity
- 02 Freqtrade/FreqAI adapter
- 03 Feature engineering
- 04 Baseline models
- 05 Ensemble models
- 06 Walk-forward simulation
- 07 Calibration/uncertainty
- 08 Quant research / external OSS scouting

### 09-16 Context Engine

- 09 Regime classifier
- 10 Swing/pivot structure
- 11 Support/resistance zones
- 12 Fibonacci and measured-move engine
- 13 Pattern hypotheses
- 14 Cross-market/BTC context
- 15 Thesis ledger and invalidation
- 16 State replay / audit log

### 17-24 Product UI

- 17 App shell/design system
- 18 TradingView chart integration
- 19 Context overlays
- 20 Forecast fan visualization
- 21 Accuracy/calibration views
- 22 Navigation/mobile
- 23 Accessibility/performance
- 24 UI QA and visual regression

### 25-30 Internal AI Harness

- 25 Tool schemas
- 26 Context retrieval
- 27 Explanation planner
- 28 Counter-thesis/challenge agent
- 29 Memory/state summarizer
- 30 AI evaluation and hallucination tests

### 31-35 Platform

- 31 API contracts
- 32 Docker/dev environment
- 33 CI/reproducibility
- 34 telemetry/data health
- 35 benchmark registry

### 36-39 Independent QA

- 36 Leakage red team
- 37 Forecast replay red team
- 38 Dogfood/operator QA
- 39 Independent benchmark replication

## Task contract format

Every assigned task begins with a markdown contract:

```md
Task: <one outcome>
Agent: <nn>
Branch: agent/<nn>-<slug>
Inputs: <docs/code/data>
Allowed write scope: <paths>
Forbidden write scope: <paths>
Dependencies: <contracts/interfaces>
Acceptance tests: <commands + expected outcomes>
Metrics gate: <if applicable>
Docs to update: <paths>
Finish criteria: <observable result>
```

## Concurrency rules

1. No two agents may own the same file path simultaneously unless one is read-only.
2. Schema/API files have a single designated owner per batch.
3. A dependent agent must code against an accepted contract, not an imagined interface.
4. If a task discovers the contract is wrong, stop and file a contract-change proposal rather than silently diverging.
5. Long tasks should be decomposed into mergeable increments.
6. Experimental models never directly replace production defaults; they publish evaluation artifacts first.

## Continuous loop

The living-project cycle is:

`observe -> issue/task -> isolated implementation -> local tests -> simulation -> completion report -> watcher review -> integration -> live/dry observation -> new evidence -> next issue`

Watcher automatically prioritizes:

1. data corruption or leakage;
2. broken build/test;
3. accuracy regressions;
4. calibration regressions;
5. UX defects obscuring uncertainty;
6. new model ideas.

## Competition mode

For uncertain research questions, Agent 00 may assign the same objective to 2-5 agents using different approaches. Examples:

- pivot algorithms;
- support-zone clustering;
- model family comparison;
- regime definitions;
- forecast visualization.

Competitors may read the same input specification but not each other's implementation until evaluation. Agent 00 compares using the same benchmark and selects or ensembles the winner.

## Reprompt protocol

If an agent returns incomplete or weak work, Agent 00 issues a correction prompt containing:

- exact failed acceptance criterion;
- evidence of failure;
- paths allowed to change;
- tests that must pass;
- what must not be rewritten;
- maximum scope of the retry.

Reprompting is preferred to broad rewrites.

## Integration gate

A change can be integrated only when:

- Constitution compliance passes;
- tests pass;
- no data leakage is detected;
- relevant docs are updated;
- metrics do not regress outside an approved experimental branch;
- Watcher can reproduce the result;
- UI claims match evaluator output.
