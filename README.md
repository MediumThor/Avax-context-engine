# AVAX Context Engine

A living, continuously evaluated AVAX market-context and probabilistic forecasting system.

This repository combines Freqtrade/FreqAI as the quantitative research backbone with a custom context engine, custom internal AI harness, TradingView Lightweight Charts UI, persistent wiki, multi-agent build/test loops, prediction journaling, and continuous walk-forward evaluation.

Start with [`CONSTITUTION.md`](CONSTITUTION.md) and [`wiki/Home.md`](wiki/Home.md).

The Internal AI Harness is specified as a Recursive Learning Harness: causal encoder memory plus a single recurrent `LoopStep` watched by Agent 00. Read [`wiki/Recursive-Learning-Harness.md`](wiki/Recursive-Learning-Harness.md) and launch implementation agents from [`wiki/Recursive-Agent-Batch.md`](wiki/Recursive-Agent-Batch.md).
