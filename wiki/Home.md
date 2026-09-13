# Wiki Home

This repository is designed to be operated by humans and many cooperating AI agents. The wiki is the shared operational memory. It is not optional documentation.

## Start here

1. [`../CONSTITUTION.md`](../CONSTITUTION.md) — immutable project law.
2. [`../AGENTS.md`](../AGENTS.md) — universal agent protocol.
3. [`Architecture.md`](Architecture.md) — system boundaries and data flow.
4. [`Agent-Orchestration.md`](Agent-Orchestration.md) — how up to 40 agents work concurrently.
5. [`Watcher-Directive.md`](Watcher-Directive.md) — Agent 00 review/correction loop.
6. [`Agent-Roster.md`](Agent-Roster.md) — prototype on `main` + recursive agent kill switch.
7. [`Agent-Launch-Pack.md`](Agent-Launch-Pack.md) — copy-ready directives for Agents 00-39.

## Subsystem directives

- [`Context-Engine-Directive.md`](Context-Engine-Directive.md)
- [`AI-Harness-Directive.md`](AI-Harness-Directive.md)
- [`Recursive-Learning-Harness.md`](Recursive-Learning-Harness.md) — encoder + all-token recurrent loop
- [`Recursive-Loop-Spec.md`](Recursive-Loop-Spec.md)
- [`Recursive-Memory-Model.md`](Recursive-Memory-Model.md)
- [`Recursive-Learning-Contracts.md`](Recursive-Learning-Contracts.md)
- [`Recursive-Evaluation.md`](Recursive-Evaluation.md)
- [`Recursive-Watcher-Protocol.md`](Recursive-Watcher-Protocol.md)
- [`Recursive-Agent-Batch.md`](Recursive-Agent-Batch.md) — launch contracts for lanes 25-30
- [`ML-FreqAI-Directive.md`](ML-FreqAI-Directive.md)
- [`UI-Directive.md`](UI-Directive.md)
- [`Navigation-Directive.md`](Navigation-Directive.md)
- [`Operability-Directive.md`](Operability-Directive.md)
- [`Testing-Directive.md`](Testing-Directive.md)
- [`Dogfooding-Directive.md`](Dogfooding-Directive.md)
- [`Simulation-Accuracy.md`](Simulation-Accuracy.md)
- [`Data-Contracts.md`](Data-Contracts.md)
- [`Prediction-Journal.md`](Prediction-Journal.md)
- [`Market-State-Spec.md`](Market-State-Spec.md)
- [`Build-Roadmap.md`](Build-Roadmap.md)
- [`Open-Source-Dependencies.md`](Open-Source-Dependencies.md)
- [`Task-Contract-Template.md`](Task-Contract-Template.md)

## Permanent regression case

The September 2026 AVAX move from the ~$8 failed-breakout region into the low-$7 area is a permanent regression scenario. The system must demonstrate that it does not repeatedly reinterpret structural deterioration as a bullish retest after explicit invalidation has occurred.

## Core product loop

`market data -> normalized event stream -> timeframe state -> structural context -> FreqAI/model ensemble -> frozen EncoderMemory -> next-10-candle forecast -> Recursive Learning Harness loop -> UI + prediction journal + LoopTrace -> realized outcomes -> evaluator / depth ablation -> watcher -> improvement queue`

The project is intentionally living: every forecast produces a future labeled example; every labeled example can improve evaluation; every proposed improvement is tested; only evidence-gated improvements are promoted.
