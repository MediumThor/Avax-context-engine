# Open-Source Research Log

**Status:** Current survey record (documentation only).  
**Survey date:** 2026-09-13 (UTC).  
**Agent:** 08 (WAVE2-08, quant research / external OSS scout).  
**Base `main` SHA:** `b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7`.  
**Isolation branch:** `cursor/wave2-08-oss-log-10e3`.  
**Allowed write scope for this task:** this file only.

This page records license, exact inspected version or commit, maintenance signal, purpose, integration boundary, and Constitution fit **before** any new dependency is recommended. It does **not** add, pin, vendor, or install packages. It does **not** claim that any library will improve forecast accuracy.

Related accepted boundary page: [`Open-Source-Dependencies.md`](Open-Source-Dependencies.md). Forecast rules: [`ML-FreqAI-Directive.md`](ML-FreqAI-Directive.md). Evaluation rules: [`Simulation-Accuracy.md`](Simulation-Accuracy.md). Immutable law: [`../CONSTITUTION.md`](../CONSTITUTION.md).

## Task contract (embedded)

A separate contract file was not created: Agent 00 limited this lane to one path.

| Field | Value |
| --- | --- |
| Task | Survey maintained OSS ML / time-series / crypto research projects that could later help data, features, evaluation, drift detection, or training. Record evidence before any dependency recommendation. |
| Agent | 08 |
| Base | latest `origin/main` at `b6bbbf4dccb6bdd4dc98473ab4887679e282b8b7` |
| Isolation | temporary branch `cursor/wave2-08-oss-log-10e3` |
| Integration target | `main` via Watcher |
| Inputs | Constitution; `wiki/Home.md`; `wiki/ML-FreqAI-Directive.md`; `wiki/Open-Source-Dependencies.md`; `upstream.lock.json`; `pyproject.toml`; GitHub REST metadata via `gh` |
| Allowed write scope | `wiki/Open-Source-Research-Log.md` |
| Forbidden write scope | `CONSTITUTION.md`; any code, lockfiles, adapters, CI; adding or installing project dependencies |
| Dependencies | none |
| Acceptance tests | this page exists; every required category is covered; no other files changed; no accuracy claims |
| Metrics gate | none (research log only) |
| Finish criteria | committed and pushed research log; Watcher may open the PR |

## How to read this log

Recommendation vocabulary (this page only; **not** an add-dep instruction):

| Recommendation | Meaning |
| --- | --- |
| `watch` | Keep surveying. Do not add. Useful as a reference or later candidate if maintenance and Constitution tests still hold. |
| `adapter-later` | Could be consumed behind an explicit adapter after a later pin, license review, and leakage/execution tests. **Not added in this task.** |
| `reject` | Do not use as a dependency or vendor for the stated purpose. |

Integration-boundary vocabulary:

| Boundary | Meaning |
| --- | --- |
| `adapter` | Consume through a thin, versioned wrapper. Do not copy upstream files into custom modules. |
| `vendor` | Clone/pin a complete upstream tree (Freqtrade-style). Requires `upstream.lock.json` and license notices. |
| `already-declared` | Present as a loose lower bound in `pyproject.toml` on the surveyed `main` SHA. This task does not pin or expand it. |
| `do-not-use` | Must not enter the runtime, feature path, evaluator, or training stack. |
| `citation-only` | Idea/pattern reference. No code or weights. |

Inspection method:

- GitHub repository, license, release, and commit metadata were read with `gh api` on 2026-09-13.
- No candidate was `pip install`ed into this repository.
- Annotated tags were peeled to the underlying commit SHA when GitHub reported `object.type=tag`.
- Where a license file is non-SPDX (`NOASSERTION`), the first lines of the upstream license file were read.
- Popularity (stars) is recorded only as a maintenance hint. It is **not** a reason to add a library.

## Required-coverage findings

These four questions were mandatory. Answers are evidence, not promotions.

| Required topic | Finding | Recommendation |
| --- | --- | --- |
| Freqtrade / FreqAI | Already pinned at `c064be5325ad6941a2789add795434e6a13dffe9` (GPLv3). Record boundary only. | already accepted as `adapter` + vendored pin; do not re-add |
| Leakage-safe feature library | **None found.** No maintained library encodes Constitution `known_at`, completed higher-timeframe candles, and confirmed-pivot availability. Closest windowing tool (`tsflex`) is stale and still caller-responsible. | `reject` as a feature vendor; keep custom Agent 03 features |
| Walk-forward / eval library | **None found** that implements append-only journal-before-outcome, Constitution metric names, regime slices, or leakage probes. `sktime` splitters are the best *primitive* to study later. | custom Evaluation Engine remains required; `sktime` = `adapter-later` for splitters only |
| Drift detection | `river` 0.26.1 exposes ADWIN / Page-Hinkley / KSWIN under BSD-3-Clause and is actively released. | `watch` now; `adapter-later` only after a pin and chronology-safe tests |
| Crypto data source besides inventing a scraper | Binance public bulk dumps (`data.binance.vision`, documented by `binance/binance-public-data`) plus the existing Vision REST helper. `ccxt` is a maintained unified public-market client with an execution surface that MUST stay disabled. | dumps = `adapter-later`; `ccxt` = `watch` with read-only hard boundary |

This page MUST NOT be read as permission to add a dependency, enable exchange orders, or report a forecast-accuracy gain.

## Recommendation summary

| # | Project | Purpose | Inspected pin | Recommendation |
| --- | --- | --- | --- | --- |
| 1 | [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | training / data backbone | `c064be5325ad6941a2789add795434e6a13dffe9` | boundary only (already pinned) |
| 2 | [freqtrade/technical](https://github.com/freqtrade/technical) | features (Freqtrade-adjacent) | `1.7.0` / `c3fc191961cb20e3c6cb9d8de8866a983dc340d7` | `watch` |
| 3 | [predict-idlab/tsflex](https://github.com/predict-idlab/tsflex) | features (windowed) | `v0.4.1` / `6043498f31bf6069d20dde6b1ee912c45ae707cc` | `watch` (stale; not leakage-safe by itself) |
| 4 | [blue-yonder/tsfresh](https://github.com/blue-yonder/tsfresh) | features | `v0.21.2` / `6aa24fdef7e3c3f48b19482535693f5796f2b598` | `reject` as feature vendor |
| 5 | [bukosabino/ta](https://github.com/bukosabino/ta) | features | `0.11.0` / `565478298cb1d9c8461d69b0296d28e999c1b0ae` | `reject` |
| 6 | [freqtrade/pandas-ta](https://github.com/freqtrade/pandas-ta) | features | `0.3.16` / `d06d4dcc1b97d082fa3abcd9c931216e61802245` | `reject` as leakage-safe lib |
| 7 | [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | features | `0.6.52` / `cd17af4088d68eb3d54f2ecc254d4b18f273b676` | `reject` |
| 8 | [TA-Lib/ta-lib-python](https://github.com/TA-Lib/ta-lib-python) | features | `v0.7.1` / `a9ff1b47b3ddbd57274116645d688c0ed677338b` | `reject` as leakage-safe lib |
| 9 | [feature-engine/feature_engine](https://github.com/feature-engine/feature_engine) | features | `v1.9.4` / `329dcb7fc2bfac91f25c458f6e9f9e0cdaf1283c` | `watch` |
| 10 | [sktime/sktime](https://github.com/sktime/sktime) | eval / walk-forward primitives | `v1.1.0` / `918fa838d99eb3703fe9bc963891619608aa35b4` | `adapter-later` (splitters only) |
| 11 | [Nixtla/mlforecast](https://github.com/Nixtla/mlforecast) | eval / training | `v1.1.0` / `a1609efddf8cf1a83510a50cd5487b66f32271c6` | `watch` |
| 12 | [unit8co/darts](https://github.com/unit8co/darts) | eval / training | `0.47.0` / `3d4c9e796216dd51e382e946dee5334aff4aa336` | `watch` |
| 13 | [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | eval / backtest | `v1.1.0` / `259d2d89fe2e7638baf3ca76c394937cd32b656d` | `reject` |
| 14 | [online-ml/river](https://github.com/online-ml/river) | drift | `0.26.1` / `64285b9dd6c606804753235fe992bcf25b9856ee` | `watch` → later `adapter-later` |
| 15 | [evidentlyai/evidently](https://github.com/evidentlyai/evidently) | drift / eval reports | `v0.7.23` / `74f4243e4e20265e2ae61beb5a613f436607a6a3` | `watch` |
| 16 | [SeldonIO/alibi-detect](https://github.com/SeldonIO/alibi-detect) | drift | `v0.13.0` / `3c215893df5f6e2b3845d8458ac819a4ab884859` | `reject` |
| 17 | [NannyML/nannyml](https://github.com/NannyML/nannyml) | drift | `v0.13.1` / `4c86ee350dc541cb244f965cf555b4b2a004ae99` | `watch` |
| 18 | [binance/binance-public-data](https://github.com/binance/binance-public-data) | data | `5c7f3197591c0d54d85dc43066226bc4c671d47a` | `adapter-later` |
| 19 | [ccxt/ccxt](https://github.com/ccxt/ccxt) | data (unified exchange API) | `v4.5.78` / `1bcb68e1d7a487c581e0e3cfae011f121649d726` | `watch` (read-only only) |
| 20 | [bmoscon/cryptofeed](https://github.com/bmoscon/cryptofeed) | data (live websocket) | `v2.5.0` / `5876430854d39c588dd9eec17707e84addb720ff` | `reject` for v1 |
| 21 | [tardis-dev/tardis-python](https://github.com/tardis-dev/tardis-python) | data (tick replay client) | `5.0.0` / `58ec503a252126655f07ae6b829c52e5c9dce90f` | `reject` as data vendor |
| 22 | [coinmetrics/api-client-python](https://github.com/coinmetrics/api-client-python) | data | `2025.9.9.13` / latest inspected commit `5f3752667b14` | `reject` |
| 23 | [microsoft/qlib](https://github.com/microsoft/qlib) | training / eval platform | `v0.9.7` / `da920b7f954f48ab1bb64117c976710de198373e` | `reject` as platform vendor |
| 24 | [hudson-and-thames/mlfinlab](https://github.com/hudson-and-thames/mlfinlab) | features / eval | last meaningful commit `79dcc7120ec8` (2021-12-01) | `reject` |
| 25 | numpy (already declared) | training plumbing | latest inspected release `v2.5.3` / `dd88c0c19b54ad9ed3533224221285bf0873249a` | `already-declared`; pin later, not this task |
| 26 | pandas (already declared) | data / features plumbing | latest inspected release `v3.0.5` / `e68db09ecf6427d1b62e565bacf17f2e525a3032` | `already-declared`; pin later, not this task |
| 27 | scikit-learn (already declared) | training / eval plumbing | latest inspected release `1.9.1` / `866c0f51e7560ef0303cbcc5f159df5382ea9e3f` | `already-declared`; pin later, not this task |
| 28 | LightGBM (already declared) | training | latest inspected release `v4.7.0` / `8f7036f03627054d5a54a6f965b13f4b9ff2cb63` | `already-declared`; pin later, not this task |
| 29 | XGBoost (already declared) | training | latest inspected release `v3.4.1` / `6fe8c547bdd21c73e4555d85b087d9260595d30d` | `already-declared`; pin later, not this task |
| 30 | [catboost/catboost](https://github.com/catboost/catboost) | training | `v1.2.10` / `b1bd2a6d77219e82a1acfcedfccb8e6f6c1ee084` | `watch` |
| 31 | [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | training (Tier 0/1 baselines) | `v0.15.0` / `278ff9950636cdd4939b4055e339a8e681d79cab` | `watch` |
| 32 | [optuna/optuna](https://github.com/optuna/optuna) | training (HPO) | `v5.0.0` / `01ddd17ab9f36c3d2817aed9afe376e1cb047d35` | `watch` |
| 33 | [pytorch/pytorch](https://github.com/pytorch/pytorch) | training (Tier 3 later) | `v2.14.0` / `2b3ec34829036a65cd9d1398ea72a0167dc37470` | `watch` |
| 34 | [sktime/pytorch-forecasting](https://github.com/sktime/pytorch-forecasting) | training | `v1.8.0` / `4d8d97cd3e85a15a9b90a38dfb0afc819d8e8aa4` | `watch` |
| 35 | [Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) | training | `v3.2.2` / `d3872423f105c7abec874a23901cb6a2060c00c5` | `watch` |
| 36 | [awslabs/gluonts](https://github.com/awslabs/gluonts) | training / eval | `v0.17.0` / `99eb407d7dd8bd5726738a8fb409560d86d19de0` | `watch` |
| 37 | [mlflow/mlflow](https://github.com/mlflow/mlflow) | training registry | `v3.16.0` / `998f7103eb5bb305491aa6e661e3862af0a8a8ed` | `watch` |

**Candidates counted:** 37 inspected rows. **Dependencies added this task:** 0.

## 1. Freqtrade / FreqAI — already pinned (boundary only)

Freqtrade/FreqAI is infrastructure, not the Context Engine, Evaluation Engine, or Internal AI Harness ([Constitution §11](../CONSTITUTION.md)). This task does not change the pin.

| Field | Record |
| --- | --- |
| Project + URL | [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) |
| License | GNU GPL v3 (`LICENSE` at the pin begins “GNU GENERAL PUBLIC LICENSE / Version 3, 29 June 2007”). SPDX from GitHub: `GPL-3.0`. |
| Exact version inspected | Commit `c064be5325ad6941a2789add795434e6a13dffe9` (message: “chore: move comment to docstring”, committer date 2026-09-13T06:45:02Z). Recorded in `upstream.lock.json` and [`Open-Source-Dependencies.md`](Open-Source-Dependencies.md). |
| Maintenance signal | Not archived. Latest upstream release at survey time: `2026.8` published 2026-08-31. Default branch `develop` had later commits the same day as the pin (`pushed_at` 2026-09-13T06:57:02Z). Pin is a specific commit, not “latest”. |
| Purpose | data / features plumbing / training / research backtests through FreqAI. |
| Integration boundary | `adapter` under `adapters/freqtrade/` plus complete-repo vendor clone via bootstrap. Do not copy arbitrary upstream files. Do not replace the custom Context Engine or RLH with FreqAI narrative. |
| Constitution fit | **Leakage risk:** FreqAI feature pipelines can use unfinished candles or future-aware indicators unless the adapter and our feature layer enforce `known_at` and completed parent candles. **Shuffle risk:** any random split around FreqAI training is prohibited for reported performance. **Execution risk:** Freqtrade can place live orders. v1 MUST remain dry/read-only; no real trading keys ([Constitution §17](../CONSTITUTION.md)). **Copyleft risk:** GPLv3 obligations apply to a combined derivative distribution; keep the adapter boundary and preserve notices. |
| Recommendation | Boundary already accepted. Do not add a second copy. Do not bump the pin in this task. |

Satellite (not a substitute pin):

| Field | [freqtrade/technical](https://github.com/freqtrade/technical) |
| --- | --- |
| License | GPL-3.0 |
| Inspected | tag `1.7.0` commit `c3fc191961cb20e3c6cb9d8de8866a983dc340d7` (release 2026-07-21; latest commit seen 2026-09-10) |
| Purpose | features |
| Boundary | do not vendor separately; if ever used, only inside the existing Freqtrade adapter |
| Constitution fit | Same GPL and leakage caveats as Freqtrade indicators. No `known_at` contract. |
| Recommendation | `watch` |

## 2. Features — no leakage-safe library found

**Why none:** Constitution §5 and the ML directive require that every feature at forecast time `t` use only information whose `known_at <= t`, that higher-timeframe values come from **completed** parent candles, and that confirmed pivots become available at confirmation time rather than the pivot candle’s open. No inspected library implements those rules. Typical TA wrappers compute expanding/rolling indicators on a fully assembled frame; if a caller passes a series that already contains future rows, the library will happily leak. Automatic extractors (`tsfresh`) score relevance on the supplied window and will leak if that window is not strictly causal. Therefore Agent 03 MUST keep a custom leakage-safe feature snapshot. A later adapter MAY wrap a windowing helper, but only after point-in-time tests exist.

### 2.1 Closest-to-causal windowing (still not sufficient)

| Field | Record |
| --- | --- |
| Project + URL | [predict-idlab/tsflex](https://github.com/predict-idlab/tsflex) |
| License | MIT |
| Exact version inspected | `v0.4.1` commit `6043498f31bf6069d20dde6b1ee912c45ae707cc` |
| Maintenance signal | Last release and last commit 2024-09-06. Not archived, but **stale** (~24 months without a release at survey time). |
| Purpose | features (stride/window feature extraction) |
| Integration boundary | `adapter` only, if ever; do not vendor. Caller would still have to supply causal windows and HTF completion. |
| Constitution fit | **Leakage risk:** high unless every window end is `<= t` and HTF series are completed-candle only. The library does not know `known_at` or pivot confirmation. **Shuffle risk:** none inherent. **Execution risk:** none. |
| Recommendation | `watch`. Do not add while unmaintained. Not a leakage-safe feature library by itself. |

### 2.2 Feature libraries rejected as vendors

| Project + URL | License | Inspected version / commit | Maintenance signal | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [blue-yonder/tsfresh](https://github.com/blue-yonder/tsfresh) | MIT | `v0.21.2` / `6aa24fdef7e3c3f48b19482535693f5796f2b598` (release 2026-05-31; commit seen 2026-07-06) | Active enough | features | `do-not-use` as the feature engine | **Leakage:** relevance filtering and whole-series extraction leak if the frame includes future rows or labels. No HTF/`known_at` model. Shuffle-friendly APIs exist. No execution. | `reject` |
| [bukosabino/ta](https://github.com/bukosabino/ta) | MIT | `0.11.0` / `565478298cb1d9c8461d69b0296d28e999c1b0ae` | Last tag 0.11.0; last commit 2026-03-18 (README). No GitHub “latest release” object. | features | `do-not-use` | Computes TA on the supplied frame. No point-in-time contract. Easy silent overwrite of HTF state if resampled naively. | `reject` |
| [freqtrade/pandas-ta](https://github.com/freqtrade/pandas-ta) | MIT | `0.3.16` / `d06d4dcc1b97d082fa3abcd9c931216e61802245` | Fork; release 2025-09-29. Original `twopirllc/pandas-ta` returned GitHub 404 on 2026-09-13. | features | `do-not-use` as leakage-safe lib | Same whole-frame TA risk. Uncertain upstream continuity. | `reject` |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | MIT | `0.6.52` / `cd17af4088d68eb3d54f2ecc254d4b18f273b676` (release 2026-06-24) | Community continuation of pandas-ta | features | `do-not-use` | Same leakage profile. Not inspected as a pin candidate. | `reject` |
| [TA-Lib/ta-lib-python](https://github.com/TA-Lib/ta-lib-python) | BSD-2-Clause | `v0.7.1` / `a9ff1b47b3ddbd57274116645d688c0ed677338b` (release 2026-07-16; later commit 2026-08-29) | Maintained wrapper; native C library is a separate install | features | `do-not-use` as leakage-safe lib | Classic TA; no `known_at`. Native binary complicates reproducibility. | `reject` |
| [feature-engine/feature_engine](https://github.com/feature-engine/feature_engine) | BSD-3-Clause | `v1.9.4` / `329dcb7fc2bfac91f25c458f6e9f9e0cdaf1283c` (release 2026-07-21; commit seen 2026-08-30) | Maintained | features | `adapter` only if sklearn-style transformers are later needed | Fit-on-all-data leaks. Some datetime transformers are not market-`known_at` aware. | `watch` |
| [hudson-and-thames/mlfinlab](https://github.com/hudson-and-thames/mlfinlab) | Proprietary / custom (LICENSE.txt, last updated November 2021). GitHub SPDX `NOASSERTION`. | last commit `79dcc7120ec8` (2021-12-01); `pushed_at` 2023-10-02 | **Stale.** No releases. | features / purged-CV ideas | `do-not-use` | License is not OSS. Purged/combinatorial CV ideas are citable; the code is not usable here. | `reject` |

**Already-declared plumbing (not feature libraries):** `pandas` and `numpy` remain the numeric substrate. They do not provide leakage-safe market features. See §6.

## 3. Walk-forward / evaluation — no Constitution-complete library

**Why none:** The Evaluation Engine MUST be chronological, journal forecasts before outcomes, score horizons `h=1..10` with named targets, compare frozen baselines, and slice by regime ([`Simulation-Accuracy.md`](Simulation-Accuracy.md), Constitution §§5–7). Inspected forecasting libraries provide *some* expanding/sliding-window splitters or `historical_forecasts` helpers. They do not implement our journal, Context Engine fingerprints, or leakage red-team. Random `train_test_split` on rows remains available in the Python ecosystem and MUST NOT be used for reported forecasting performance.

### 3.1 Best later primitive: sktime splitters

| Field | Record |
| --- | --- |
| Project + URL | [sktime/sktime](https://github.com/sktime/sktime) |
| License | BSD-3-Clause |
| Exact version inspected | `v1.1.0` commit `918fa838d99eb3703fe9bc963891619608aa35b4` (release 2026-07-28) |
| Maintenance signal | Active. Commits on 2026-09-13. Splitter modules present at that tag (`sktime/split/expandingwindow.py`, `expandingslidingwindow.py`, `cutoff.py`, and related). |
| Purpose | eval (walk-forward *primitives*); also a full forecasting toolkit we MUST NOT adopt wholesale |
| Integration boundary | `adapter-later` for splitter ideas or a thin wrapper around chronological split objects. Do not vendor the forecasting stack. Do not let sktime become the Evaluation Engine. |
| Constitution fit | **Leakage risk:** low for the splitter objects if used only to emit `(train_end, test_start, test_end)` timestamps; high if sktime pipelines resample or generate features internally without our `known_at` rules. **Shuffle risk:** the library also contains i.i.d.-style utilities; those MUST NOT be used for reported metrics. **Execution risk:** none. |
| Recommendation | `adapter-later` (splitters only). Do not add in this task. Custom evaluator remains mandatory. |

### 3.2 Other eval / forecast toolkits

| Project + URL | License | Inspected version / commit | Maintenance signal | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Nixtla/mlforecast](https://github.com/Nixtla/mlforecast) | Apache-2.0 | `v1.1.0` / `a1609efddf8cf1a83510a50cd5487b66f32271c6` (release 2026-07-10; later dep-bump commit 2026-09-08) | Active | training / eval helpers | `do-not-use` as evaluator | Convenient lag/feature generation can leak if date indexes are wrong. Cross-validation helpers are not our journal. No execution. | `watch` |
| [unit8co/darts](https://github.com/unit8co/darts) | Apache-2.0 | `0.47.0` / `3d4c9e796216dd51e382e946dee5334aff4aa336` (release 2026-09-04; commit seen 2026-09-07) | Active | training / eval / anomaly | `do-not-use` as evaluator | Heavy stack. `historical_forecasts` is useful conceptually; still no Constitution journal or HTF rules. | `watch` |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Apache-2.0 **with Commons Clause v1.0** (LICENSE.md). Not OSI-open for “Sell”. GitHub SPDX `NOASSERTION`. | `v1.1.0` / `259d2d89fe2e7638baf3ca76c394937cd32b656d` (release 2026-07-05; later README commit 2026-08-02) | Releases exist; license is restrictive | eval / backtest / portfolio | `do-not-use` | **Execution risk:** portfolio/order simulation APIs sit next to research. Commons Clause is incompatible with a clean OSS dependency story. Shuffle/leakage not the main issue; license + trading orientation are. | `reject` |
| [awslabs/gluonts](https://github.com/awslabs/gluonts) | Apache-2.0 | `v0.17.0` / `99eb407d7dd8bd5726738a8fb409560d86d19de0` (release 2026-07-31) | Release in last ~6 weeks of survey; subsequent bump to `0.18.0dev0` | training / probabilistic eval | `do-not-use` as evaluator | Probabilistic forecasting toolkit. Can encourage dataset splits that ignore our journal. No execution. | `watch` |
| [microsoft/qlib](https://github.com/microsoft/qlib) | MIT | `v0.9.7` / `da920b7f954f48ab1bb64117c976710de198373e` (release 2025-08-15; later commit seen 2026-07-23) | Large platform; latest *release* is older than latest commits | training / eval platform | `do-not-use` | Equity-research oriented. High chance of handler-specific leakage and i.i.d. habits. Would replace too much of our spine. No v1 execution, but the platform is built around investment workflows. | `reject` |

## 4. Drift detection

Drift detectors MAY later flag feature or residual distribution change. They MUST NOT silently retune models on the same window used to report test metrics, and they MUST NOT rewrite journaled forecasts.

### 4.1 Preferred later option: River

| Field | Record |
| --- | --- |
| Project + URL | [online-ml/river](https://github.com/online-ml/river) |
| License | BSD-3-Clause |
| Exact version inspected | `0.26.1` annotated tag peels to commit `64285b9dd6c606804753235fe992bcf25b9856ee` (release 2026-08-21) |
| Maintenance signal | Active. Later commit seen 2026-09-03. At the inspected tag, `river/drift/` contains `adwin.py`, `page_hinkley.py`, `kswin.py`, plus retrain helpers. |
| Purpose | drift (and online learning — only the drift subset is in scope) |
| Integration boundary | `adapter-later`: wrap specific detectors. Do not adopt River as an online trading/learning brain. Do not vendor. |
| Constitution fit | **Leakage risk:** detectors that peek at future residuals leak. Use only information available at `t`. **Shuffle risk:** streaming detectors assume chronology; do not batch-shuffle then “detect drift”. **Execution risk:** none in the drift module. Online *model* APIs could be misused to replace walk-forward; that would be a Constitution miss. |
| Recommendation | `watch` now. Eligible for a later adapter **after** an exact pin and tests that detectors cannot see future labels. This task does not add it. |

### 4.2 Other drift options

| Project + URL | License | Inspected version / commit | Maintenance signal | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [evidentlyai/evidently](https://github.com/evidentlyai/evidently) | Apache-2.0 | `v0.7.23` / `74f4243e4e20265e2ae61beb5a613f436607a6a3` (release 2026-09-11) | Very active | drift / reports | `adapter-later` only as an offline report renderer | Batch drift reports can leak if reference/current windows are wrong. Dashboard-oriented. No execution. | `watch` |
| [NannyML/nannyml](https://github.com/NannyML/nannyml) | Apache-2.0 | `v0.13.1` / `4c86ee350dc541cb244f965cf555b4b2a004ae99` (release 2025-07-12) | Last release ~14 months before survey | drift / performance estimation | `do-not-use` until maintenance is re-verified | Performance estimation that uses outcomes after `t` is not a live feature. No execution. | `watch` |
| [SeldonIO/alibi-detect](https://github.com/SeldonIO/alibi-detect) | Business Source License 1.1 (not OSI-open for production). Change license Apache-2.0 four years after each version. Additional grant for non-profit education only. | `v0.13.0` / `3c215893df5f6e2b3845d8458ac819a4ab884859` (release 2025-12-11) | Release exists; quieter than River | drift | `do-not-use` | License blocks production use. Technical drift methods are citable only. | `reject` |

## 5. Crypto data sources (no new scraper invented)

**Current (already on `main`):** `packages/market_data/binance.py` talks to `https://data-api.binance.vision` for klines. That is a public REST helper, not an OSS library pin.

A second source MUST be a documented public dataset or a maintained client, not an ad-hoc HTML scraper.

### 5.1 Preferred later bulk source: Binance public data dumps

| Field | Record |
| --- | --- |
| Project + URL | [binance/binance-public-data](https://github.com/binance/binance-public-data) documenting dumps at [https://data.binance.vision/](https://data.binance.vision/) |
| License | **No repository license file** (GitHub `license: unknown` / license API 404). Data terms are Binance’s public-data terms, not an OSS license. Treat as an external data source, not a code dependency. |
| Exact version inspected | Commit `5c7f3197591c0d54d85dc43066226bc4c671d47a` (2025-01-09, microseconds note). **Not a software pin.** |
| Maintenance signal | Repo last pushed 2025-01-09. The *data site* is what matters; dump freshness was **not** verified by downloading files in this task (no new data vendor, no scraper). Honesty: dump-site liveness is unknown from GitHub metadata alone. |
| Purpose | data (daily/monthly spot and futures klines, aggTrades, trades — including `5m`) |
| Integration boundary | `adapter-later` inside `packages/market_data/`: download immutable files, checksum, store under the existing manifest/store contract. Do not import the repo’s sample `python/` scripts as product code. |
| Constitution fit | **Leakage risk:** files are published next day (daily) or later (monthly). Live 5m features MUST NOT assume a dump is complete through “now”. Use `known_at` = file publication / close time, not candle open. **Shuffle risk:** none. **Execution risk:** none (read-only dumps). |
| Recommendation | `adapter-later` as the first additional source besides the existing Vision REST client. Do not invent a scraper. Do not add a Python dependency for this. |

### 5.2 Unified public-market client (execution surface present)

| Field | Record |
| --- | --- |
| Project + URL | [ccxt/ccxt](https://github.com/ccxt/ccxt) |
| License | MIT (`LICENSE.txt`) |
| Exact version inspected | `v4.5.78` peels to commit `1bcb68e1d7a487c581e0e3cfae011f121649d726` (release 2026-09-07; repo still receiving automated commits on 2026-09-13) |
| Maintenance signal | Actively maintained. |
| Purpose | data (unified public OHLCV / ticker). Also a full **trading** API. |
| Integration boundary | `adapter` with a hard read-only wrap **if** ever added: allow public fetch only; refuse `create_order` / withdraw / private account calls; no trading keys in v1. Prefer remaining on Binance public endpoints first. |
| Constitution fit | **Execution risk: high** if imported casually — CCXT’s purpose includes order placement. Constitution §17 forbids real trades in v1. **Leakage risk:** using unclosed klines as closed observations. **Shuffle risk:** none. |
| Recommendation | `watch`. Do not add in this task. A later adapter is allowed only with execution APIs unusable and tests that prove it. |

### 5.3 Other data clients

| Project + URL | License | Inspected version / commit | Maintenance signal | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [bmoscon/cryptofeed](https://github.com/bmoscon/cryptofeed) | GNU **AGPL v3** plus §7 attribution term (LICENSE). GitHub SPDX `NOASSERTION`. | `v2.5.0` / `5876430854d39c588dd9eec17707e84addb720ff` (release 2026-08-09; later commit 2026-09-08) | Active | data (live websocket) | `do-not-use` in v1 | AGPL copyleft is heavier than Freqtrade’s GPL for a combined network service. Live feeds are freshness, not historical research. No need for another execution-adjacent socket stack. | `reject` for v1 |
| [tardis-dev/tardis-python](https://github.com/tardis-dev/tardis-python) | MPL-2.0 | `5.0.0` / `58ec503a252126655f07ae6b829c52e5c9dce90f` (release 2026-08-23) | Client maintained | data (tick/L2 replay **client**) | `do-not-use` | Client is OSS; **data access is a commercial API**. Not a substitute public source. No execution if only replaying files, but it is not free public history. | `reject` as data vendor |
| [coinmetrics/api-client-python](https://github.com/coinmetrics/api-client-python) | MIT (client) | tag `2025.9.9.13` (2025-09-10); commit seen `5f3752667b14` (2025-10-02) | Quiet | data | `do-not-use` | Client MIT; community/commercial data terms are separate and were not accepted here. | `reject` |

## 6. Already-declared training / plumbing (do not expand this task)

`pyproject.toml` on the surveyed `main` SHA already declares loose lower bounds. This task does **not** pin them and does **not** add extras. Exact **resolved** wheels in any local environment were not treated as pins.

| Project + URL | License (upstream) | Latest inspected release / commit | Declared in repo | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [numpy/numpy](https://github.com/numpy/numpy) | BSD-style (LICENSE.txt; GitHub SPDX `NOASSERTION`) | `v2.5.3` / `dd88c0c19b54ad9ed3533224221285bf0873249a` (2026-09-06) | `numpy>=2.1` | training plumbing | `already-declared` | No inherent leakage. | pin later (Agent 33/02), not now |
| [pandas-dev/pandas](https://github.com/pandas-dev/pandas) | BSD-3-Clause | `v3.0.5` / `e68db09ecf6427d1b62e565bacf17f2e525a3032` (2026-07-22) | `pandas>=2.2` | data / features plumbing | `already-declared` | Rolling ops leak if the frame contains future rows. | pin later, not now |
| [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | BSD-3-Clause | `1.9.1` / `866c0f51e7560ef0303cbcc5f159df5382ea9e3f` (2026-09-11) | `scikit-learn>=1.5` | training / metrics | `already-declared` | `train_test_split` shuffle is forbidden for reported forecast metrics. Scalers MUST fit inside each walk-forward train window only. | pin later, not now |
| [lightgbm-org/LightGBM](https://github.com/lightgbm-org/LightGBM) (GitHub redirects from `microsoft/LightGBM`) | MIT | `v4.7.0` / `8f7036f03627054d5a54a6f965b13f4b9ff2cb63` (2026-07-18; later commit 2026-09-12) | `lightgbm>=4.5` | training (Tier 2) | `already-declared` | No accuracy claim. Must beat baselines out of sample before promotion. | pin later, not now |
| [dmlc/xgboost](https://github.com/dmlc/xgboost) | Apache-2.0 | `v3.4.1` / `6fe8c547bdd21c73e4555d85b087d9260595d30d` (2026-08-15; later commit 2026-09-11) | `xgboost>=2.1` | training (Tier 2) | `already-declared` | Same as LightGBM. | pin later, not now |

## 7. Training candidates not in the repo (watch only)

None of these are added. None are claimed to beat baselines.

| Project + URL | License | Inspected version / commit | Maintenance signal | Purpose | Boundary | Constitution fit | Rec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [catboost/catboost](https://github.com/catboost/catboost) | Apache-2.0 | `v1.2.10` / `b1bd2a6d77219e82a1acfcedfccb8e6f6c1ee084` (release 2026-02-19; later commits 2026-09-12) | Code active; latest *release* older than HEAD | training | `adapter-later` only if Agent 05 justifies a third booster | Same walk-forward / no-shuffle rules. No execution. | `watch` |
| [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | BSD-3-Clause | `v0.15.0` / `278ff9950636cdd4939b4055e339a8e681d79cab` (release 2026-08-27; commit seen 2026-09-12) | Active | training (simple statistical baselines) | `adapter-later` for Tier 0/1 | Useful for honest baselines. In-sample fit MUST NOT be reported as accuracy. | `watch` |
| [optuna/optuna](https://github.com/optuna/optuna) | MIT | `v5.0.0` / `01ddd17ab9f36c3d2817aed9afe376e1cb047d35` (release 2026-09-07) | Active | training (HPO) | `adapter-later` | **Leakage / goalpost risk:** tuning on the reported test window is forbidden. Search must stay inside each walk-forward train/validation split. | `watch` |
| [pytorch/pytorch](https://github.com/pytorch/pytorch) | BSD-style (LICENSE; GitHub SPDX `NOASSERTION`) | `v2.14.0` / `2b3ec34829036a65cd9d1398ea72a0167dc37470` (release 2026-09-02) | Very active | training (Tier 3 later) | `adapter-later` only after tabular baselines exist | Sequence models can leak via future padding or target shift. No execution. Do not assume Tier 3 beats Tier 2. | `watch` |
| [sktime/pytorch-forecasting](https://github.com/sktime/pytorch-forecasting) | MIT | `v1.8.0` / `4d8d97cd3e85a15a9b90a38dfb0afc819d8e8aa4` (release 2026-06-24; later dependabot 2026-09-11) | Maintained under sktime org | training (TFT-class) | `do-not-use` until Tier 2 gates exist | High leakage surface (known-future covariates). | `watch` |
| [Nixtla/neuralforecast](https://github.com/Nixtla/neuralforecast) | Apache-2.0 | `v3.2.2` / `d3872423f105c7abec874a23901cb6a2060c00c5` (release 2026-09-08) | Active | training | `do-not-use` until Tier 2 gates exist | Same as other sequence toolkits. | `watch` |
| [mlflow/mlflow](https://github.com/mlflow/mlflow) | Apache-2.0 | `v3.16.0` / `998f7103eb5bb305491aa6e661e3862af0a8a8ed` (release 2026-09-04) | Active | training registry | `watch`; prefer a small internal experiment manifest first ([`Simulation-Accuracy.md`](Simulation-Accuracy.md)) | Registry must not overwrite journals. No execution. | `watch` |

## 8. Citation-only (already recorded elsewhere)

The Recurrent Looped Transformer report remains **citation-only** on [`Open-Source-Dependencies.md`](Open-Source-Dependencies.md). This survey did not re-pin or vendor that repository. Prefer re-implementing the RLH loop contract over forking.

## 9. What this survey explicitly does not do

- Does not add or pin any dependency.
- Does not install packages into the project environment as deps.
- Does not claim any library will improve forecast accuracy, calibration, or trading PnL.
- Does not enable Freqtrade, CCXT, or any other execution path.
- Does not replace the custom Context Engine with an LLM or with Qlib/Darts/sktime.
- Does not treat star counts as an intake reason.

## 10. Suggested later intake order (Watcher / later agents)

These are sequencing hints, not work authorized by this file:

1. Keep Freqtrade at the existing pin; Agent 02 owns any bump.
2. Agent 03: custom leakage-safe features. Do not import TA libraries to “save time”.
3. Agent 06: custom walk-forward Evaluation Engine. Optionally study `sktime` splitter semantics; do not add the package until a bounded contract says so.
4. Agent 01: optional Binance dump downloader (HTTP files + checksums), not a new scraper and not CCXT.
5. After evaluator gates exist: consider a River drift **adapter** with an exact pin.
6. Pin already-declared numeric/ML lower bounds in a reproducibility task (Agent 33), separately from this log.

## 11. Documentation / contract impact

| Item | Change |
| --- | --- |
| Schema / API contracts | none |
| `upstream.lock.json` | unchanged |
| `pyproject.toml` | unchanged |
| `CONSTITUTION.md` | unchanged |
| This wiki page | created |

Relative links in this page: `Open-Source-Dependencies.md`, `ML-FreqAI-Directive.md`, `Simulation-Accuracy.md`, `../CONSTITUTION.md`.

## 12. Known limitations of this survey

- PyPI yanked/retracted wheels were not exhaustively checked.
- Binance dump-site availability and AVAXUSDT file completeness were not downloaded (out of scope; would be Agent 01 work).
- `twopirllc/pandas-ta` is gone from GitHub; only forks were inspectable.
- Commons Clause, AGPL, BSL, and Coinmetrics/Tardis data terms were read from license files / repo docs, not from legal counsel.
- Maintenance “active” means GitHub dates, not a quality judgment.
- No out-of-sample model comparison was run. None should be inferred.
