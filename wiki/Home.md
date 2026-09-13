# Wiki Home

This wiki is the versioned operating memory for AVAX Context Engine. It defines project law, current implementation status, target behavior, machine contracts, agent ownership, and evidence gates.

> **Current state:** `main` contains an integrated prototype, not a finished platform. See [`Agent-Build-Plan.md`](Agent-Build-Plan.md) for a code-verified inventory and remaining gates. Described behavior is a target requirement unless the page or build plan identifies an implemented and tested path.

## Authority order

When sources disagree, stop and open a correction task. Apply this order:

1. [`../CONSTITUTION.md`](../CONSTITUTION.md) — immutable project law.
2. Implemented canonical schemas and their contract tests.
3. [`Data-Contracts.md`](Data-Contracts.md), [`Market-State-Spec.md`](Market-State-Spec.md), [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md), and [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md).
4. Subsystem directives.
5. [`Architecture.md`](Architecture.md) — component boundaries and data flow.
6. [`Agent-Build-Plan.md`](Agent-Build-Plan.md) and [`Build-Roadmap.md`](Build-Roadmap.md) — status, dependencies, and delivery sequence.
7. Launch prompts, task templates, landing pages, and prose summaries.

No lower-authority source may weaken the Constitution, schema tests, chronology rules, journal immutability, kill switch, or no-execution boundary.

## Before any agent work

1. Read [`../CONSTITUTION.md`](../CONSTITUTION.md), [`../AGENTS.md`](../AGENTS.md), and [`Documentation-Standards.md`](Documentation-Standards.md).
2. Pull and record the latest `main` SHA.
3. Read [`Agent-Build-Plan.md`](Agent-Build-Plan.md), [`Agent-Orchestration.md`](Agent-Orchestration.md), and the relevant subsystem directive.
4. Check [`Agent-Roster.md`](Agent-Roster.md), active Watcher artifacts, path ownership, and dependencies.
5. For RLH work, check the operator kill switch. If engaged, stop.
6. Create or update a bounded contract from [`Task-Contract-Template.md`](Task-Contract-Template.md).

## Reading paths

### Build the AVAX data/context/forecast spine

1. [`Architecture.md`](Architecture.md)
2. [`Data-Contracts.md`](Data-Contracts.md)
3. [`Context-Engine-Directive.md`](Context-Engine-Directive.md)
4. [`Market-State-Spec.md`](Market-State-Spec.md)
5. [`ML-FreqAI-Directive.md`](ML-FreqAI-Directive.md)
6. [`Prediction-Journal.md`](Prediction-Journal.md)
7. [`Simulation-Accuracy.md`](Simulation-Accuracy.md)

### Build or review the Recursive Learning Harness

1. [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md)
2. [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md)
3. [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md)
4. [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md)
5. [`Recursive-Evaluation.md`](Recursive-Evaluation.md)
6. [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md)
7. [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md)

### Build the mobile-first operator experience

1. [`UI-Directive.md`](UI-Directive.md)
2. [`Navigation-Directive.md`](Navigation-Directive.md)
3. [`AI-Harness-Directive.md`](AI-Harness-Directive.md)
4. [`Operability-Directive.md`](Operability-Directive.md)
5. [`Testing-Directive.md`](Testing-Directive.md)

### Improve the living system

1. [`Dogfooding-Directive.md`](Dogfooding-Directive.md)
2. [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md)
3. [`Prediction-Improvement-Loop.md`](Prediction-Improvement-Loop.md) — diagnose, request access, measure, iterate
4. [`Information-Gaps.md`](Information-Gaps.md) — missing series, wallets, news, macro
5. [`improvement/README.md`](improvement/README.md) — tickets, access asks, outcomes
6. [`Watcher-Directive.md`](Watcher-Directive.md)
7. [`Recursive-Evaluation.md`](Recursive-Evaluation.md)

## Documentation map

| Area | Primary sources |
| --- | --- |
| Governance | [`../CONSTITUTION.md`](../CONSTITUTION.md), [`../AGENTS.md`](../AGENTS.md), [`Documentation-Standards.md`](Documentation-Standards.md) |
| Current build | [`Agent-Build-Plan.md`](Agent-Build-Plan.md), [`Build-Roadmap.md`](Build-Roadmap.md), [`Agent-Roster.md`](Agent-Roster.md) |
| Architecture/dependencies | [`Architecture.md`](Architecture.md), [`Open-Source-Dependencies.md`](Open-Source-Dependencies.md), [`Operability-Directive.md`](Operability-Directive.md) |
| Core state/contracts | [`Data-Contracts.md`](Data-Contracts.md), [`Context-Engine-Directive.md`](Context-Engine-Directive.md), [`Market-State-Spec.md`](Market-State-Spec.md) |
| Forecast/evaluation | [`ML-FreqAI-Directive.md`](ML-FreqAI-Directive.md), [`Prediction-Journal.md`](Prediction-Journal.md), [`Simulation-Accuracy.md`](Simulation-Accuracy.md) |
| Recursive harness | [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md), [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md), [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md), [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md), [`Recursive-Evaluation.md`](Recursive-Evaluation.md) |
| Product interface | [`UI-Directive.md`](UI-Directive.md), [`Navigation-Directive.md`](Navigation-Directive.md), [`AI-Harness-Directive.md`](AI-Harness-Directive.md) |
| Agent operations | [`Agent-Orchestration.md`](Agent-Orchestration.md), [`Watcher-Directive.md`](Watcher-Directive.md), [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md), [`Agent-Launch-Pack.md`](Agent-Launch-Pack.md), [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md), [`Task-Contract-Template.md`](Task-Contract-Template.md), [`tasks/`](tasks/) |
| Learning/quality | [`Continuous-Improvement-Directive.md`](Continuous-Improvement-Directive.md), [`Prediction-Improvement-Loop.md`](Prediction-Improvement-Loop.md), [`Information-Gaps.md`](Information-Gaps.md), [`Dogfooding-Directive.md`](Dogfooding-Directive.md), [`Testing-Directive.md`](Testing-Directive.md) |

## Permanent regression case

The September 2026 AVAX move from the failed-breakout region near $8 into the low-$7 area is permanent. The system must not repeatedly reinterpret structural deterioration as a bullish retest after explicit invalidation.

This benchmark demands point-in-time state discipline, not hindsight-perfect calls. Exact timestamps, source data, and expected invariants belong in the versioned fixture under `benchmarks/rlh/avax-2026-09-failed-8/`.

## Product loop

```text
closed market data -> validated observations -> Context Engine snapshot
-> frozen features/EncoderMemory -> ForecastPackage -> bounded RLH LoopTrace
-> atomic journal -> mobile-first Web App -> matured outcomes
-> Evaluation Engine -> evidence-linked improvement -> Watcher -> main
```

If a forecast cannot be improved honestly, agents name the gap and ask the owner for access instead of inventing data. Operating playbook: [`Prediction-Improvement-Loop.md`](Prediction-Improvement-Loop.md).
