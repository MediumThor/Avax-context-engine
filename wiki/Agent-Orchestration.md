# Agent Orchestration

## Objective

Operate the repository as a continuously improving multi-agent engineering system without allowing concurrency to degrade correctness.

Use [`Agent-Build-Plan.md`](Agent-Build-Plan.md) for whole-product dependencies/current status and [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md) for evidence-to-code learning.

The project defines 40 ownership lanes. Up to 40 agents may work concurrently when the runtime supports it; Agent 00 otherwise schedules dependency-safe batches within the available limit. Concurrency is useful only when write scopes, contracts, and review authority are explicit.

## Mainline operating mode

`main` is the single persistent product branch.

Agents may use isolated worktrees or temporary branches for collision avoidance, but accepted changes are integrated into `main` as soon as their bounded task passes review. There is no long-lived staging branch and no delayed release train during rapid prototyping.

The operating rule is:

`latest main -> exclusive lock or disposable isolation -> bounded tests/review -> immediate main integration -> post-integration tests -> next task`

Every new task begins from the latest `main`. Every completion report ends with the accepted `main` commit SHA. Temporary branches are implementation scratch space, not project state.

## Agent 00 — Watcher

Agent 00 is always reserved for the Watcher. It does not primarily build features. It observes work, detects conflicts, verifies evidence, reprompts weak agents, and integrates accepted work directly into `main`.

Agent 00 reads every task contract and completion report. It has authority to reject or quarantine work. It also prevents accepted work from remaining stranded on temporary branches.

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

- 17 Mobile-first app shell/design system
- 18 TradingView chart integration
- 19 Context overlays
- 20 Forecast fan visualization
- 21 Accuracy/calibration views
- 22 Navigation/mobile
- 23 Accessibility/performance
- 24 UI QA and visual regression

### 25-30 Internal AI Harness / Recursive Learning Harness

Ready-to-copy contracts: [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md). Live roster: [`Agent-Roster.md`](Agent-Roster.md). Directive: [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md).

- 25 Tool + loop schema steward
- 26 EncoderMemory builder and retrieval
- 27 Same-transition `LoopStep` / `D_φ`
- 28 Counter-thesis / challenge / invalidation loop step
- 29 SWA window and state summarizer
- 30 Loop evaluation, depth ablation, hallucination tests

### 31-35 Platform

- 31 API contracts
- 32 Docker/dev environment
- 33 CI/reproducibility
- 34 telemetry/data health
- 35 benchmark and continuous-improvement registry

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
Base: latest main
Isolation: <worktree or temporary branch if required>
Integration target: main
Inputs: <docs/code/data>
Allowed write scope: <paths>
Forbidden write scope: <paths>
Dependencies: <contracts/interfaces>
Acceptance tests: <commands + expected outcomes>
Metrics gate: <if applicable>
Docs to update: <paths>
Finish criteria: <observable result on main>
```

Store active contracts in the task system, `wiki/tasks/`, or `.cursor/plans/`. A contract is not a path lock until Agent 00 records the assignment.

## Concurrency rules

1. No two agents may own the same file path simultaneously unless one is read-only.
2. Schema/API files have a single designated owner per batch.
3. A dependent agent must code against an accepted contract already represented on `main`, not an imagined interface.
4. If a task discovers the contract is wrong, stop and file a contract-change proposal rather than silently diverging.
5. Long tasks are decomposed into increments that can be integrated into `main` quickly.
6. Experimental models never directly replace accepted defaults; they publish evaluation artifacts first.
7. Agent 00 serializes conflicting integrations and reruns relevant tests after each mainline update.
8. If a temporary branch becomes stale, reconcile onto current `main`; do not preserve stale branch semantics for convenience.

## Continuous loop

The living-project cycle is:

`observe -> evidence-linked task -> locked implementation -> tests -> simulation / loop replay -> watcher review -> main integration -> post-integration verification -> live/dry observation + LoopTrace journal -> matured LoopOutcome -> next candidate`

Watcher prioritizes:

1. data corruption or leakage;
2. broken build/test;
3. accuracy regressions;
4. calibration regressions;
5. UX defects obscuring uncertainty;
6. new model ideas.

## Competition mode

For uncertain research questions, Agent 00 may assign the same objective to 2-5 agents using different approaches. Competitors remain isolated until evaluation, but only the selected or deliberately ensembled result is integrated into `main`.

Examples:

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

A change can be integrated into `main` only when:

- Constitution compliance passes;
- required tests pass;
- no data leakage is detected;
- relevant docs are updated;
- metrics do not regress outside an explicitly experimental task;
- Watcher can reproduce the result;
- Web App claims match Evaluation Engine output.

After integration, the relevant smoke/regression tests run against `main`. If they fail, the Watcher fixes or reverts the bounded change immediately rather than allowing a broken mainline to accumulate.
