# Freqtrade/FreqAI adapter

This directory is the integration boundary for pinned upstream Freqtrade/FreqAI. It is **not a fork**.

## Pin and license

- Upstream: `https://github.com/freqtrade/freqtrade.git`
- Commit: `c064be5325ad6941a2789add795434e6a13dffe9`
- License: GNU GPL v3 (`GPL-3.0`)
- Records: [`pin.json`](pin.json), [`LICENSE-NOTICE.md`](LICENSE-NOTICE.md)
- Repository lock (owned outside this adapter task): `upstream.lock.json`

Run `scripts/bootstrap_freqtrade.sh` to clone the **complete** upstream repository into `vendor/freqtrade` (gitignored), check out the pin, and write `vendor/freqtrade/.avax-upstream-manifest.json` with the commit and LICENSE path.

Do not copy upstream source into `packages/`. Combined distribution of a derivative work requires GPL review.

## Research / read-only only

`config.freqai.json` and `AvaxContextStrategy.py` are research scaffolding:

- `dry_run` is `true`
- `stake_amount` and `dry_run_wallet` are `0`
- `max_open_trades` is `0`
- `initial_state` is `stopped`
- `force_entry_enable` is `false`
- no exchange API keys
- spot pairs only (`AVAX/USDT`, `BTC/USDT`, `ETH/USDT`)
- FreqAI `data_split_parameters.shuffle` is `false`
- the strategy never sets entry or exit signals

`FreqtradeResearchAdapter` refuses `execute` / `place_order` / `create_order` / `buy` / `sell` and related methods. It will not construct a `freqtrade trade` command.

## What this does not claim

FreqAI is infrastructure, not a proven production model. This adapter does **not** claim that FreqAI already beats project baselines. Out-of-sample comparison is a later evaluation task.

## Research commands after bootstrap

The adapter may only construct these Freqtrade subcommands, always with this config:

- `download-data`
- `list-data`
- `backtesting`
- `list-exchanges`
- `list-timeframes`

Live trading, the Freqtrade webserver, and any exchange order API are out of scope for v1.

## WAVE2-05 research quantile path

Full FreqAI training is not required in CI. A leakage-safe LightGBM/sklearn-style
wrapper with a pure-Python fallback emits journal-ready next-10 5m quantiles:

```text
PYTHONPATH=. python adapters/freqtrade/quantiles.py --help-research
```

Or from Python:

```python
from adapters.freqtrade import FreqtradeResearchAdapter
payload = FreqtradeResearchAdapter().emit_research_quantile_forecast(candles, as_of=T)
```

Declared versions: LightGBM `>=4.5` and scikit-learn `>=1.5` when present;
otherwise `mtf_ridge_residual_quantiles.v1` (ridge on residual vs drift20 using
a compact `avax.features.mtf.v1` subset). Model id: `freqai.quantiles.research.v1`.

The payload is ForecastPackage-shaped (`q10_cum_log_return` / `q50` / `q90`,
`model_id`, `feature_schema_version`). It is not scored here and must not be
treated as an accuracy or ECE result. Watcher wires journaling/API later.
