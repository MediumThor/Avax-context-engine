# Open-Source Dependencies and Boundaries

## Freqtrade / FreqAI

Repository: `freqtrade/freqtrade`
Initial pinned commit: `c064be5325ad6941a2789add795434e6a13dffe9`
License observed: GNU GPL v3.

Use strategy:
- clone the complete upstream repository during bootstrap;
- pin the exact commit in config/manifest;
- run it as a separately identifiable quant service/backbone;
- keep custom Context Engine, evaluator, AI harness and UI behind explicit adapters/contracts;
- do not copy arbitrary upstream files into custom modules;
- preserve upstream notices and license;
- review GPL obligations before distributing a combined derivative work.

## TradingView Lightweight Charts

Repository: `tradingview/lightweight-charts`
License observed: Apache License 2.0.

Use strategy:
- consume published package in React/TypeScript web app;
- wrap it in a thin internal chart component;
- keep market logic outside rendering components;
- preserve required notices.

## Research inspiration — Recurrent Looped Transformer

Citation, not a vendored dependency:

- Yifan Zhang, *Recurrent Looped Transformer*, technical report, 12 September 2026
- https://yifanzhang-pro.github.io/recurrent-looped-tranformer/
- https://github.com/yifanzhang-pro/recurrent-looped-tranformer

We adopt the **pattern** (causal encoder, all-token recurrence, carried state + SWA KV, one transition for live/replay/train) inside the custom Recursive Learning Harness. We do not copy weights, claim superintelligence, or treat extra depth as automatically better.

License and pin must be recorded if any code from that repository is later evaluated. Prefer re-implementing the loop contract over forking.

## Candidate research libraries

Agents may evaluate, but must not add without license/version review:
- pandas / numpy / scipy
- scikit-learn
- LightGBM
- XGBoost
- CatBoost
- Optuna
- PyTorch
- statsmodels
- vectorbt or comparable research tools
- TA-Lib/pandas-ta alternatives
- River for online learning/drift experiments
- MLflow or lightweight experiment registry alternatives

## Dependency intake checklist

Before adding an OSS dependency, the proposing agent records:
- repository/package;
- exact version/commit;
- license;
- maintenance activity;
- purpose;
- alternatives considered;
- runtime/security implications;
- whether it crosses the custom/upstream architecture boundary.

Prefer well-maintained libraries for commodity plumbing and custom code for the differentiated Context Engine and AI harness.
