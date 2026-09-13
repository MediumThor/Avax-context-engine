"""Pinned Freqtrade identity and research-only command/method lists."""

from __future__ import annotations

from pathlib import Path

ADAPTER_DIR = Path(__file__).resolve().parent
REPO_ROOT = ADAPTER_DIR.parents[1]
PIN_PATH = ADAPTER_DIR / "pin.json"
CONFIG_PATH = ADAPTER_DIR / "config.freqai.json"
STRATEGY_PATH = ADAPTER_DIR / "AvaxContextStrategy.py"

PINNED_COMMIT = "c064be5325ad6941a2789add795434e6a13dffe9"
UPSTREAM_REPO = "https://github.com/freqtrade/freqtrade.git"
UPSTREAM_LICENSE = "GPL-3.0"
VENDOR_RELATIVE = "vendor/freqtrade"
VENDOR_MANIFEST_NAME = ".avax-upstream-manifest.json"

# Adapter surface that would place or manage exchange orders.
FORBIDDEN_ADAPTER_METHODS = frozenset(
    {
        "buy",
        "cancel_all_orders",
        "cancel_order",
        "create_order",
        "create_stoploss_order",
        "enter_trade",
        "execute",
        "execute_order",
        "execute_trade",
        "exit_trade",
        "force_enter",
        "force_exit",
        "live_trade",
        "place_order",
        "sell",
        "submit_order",
    }
)

# Subcommands the adapter may construct for research. `trade` is never allowed.
ALLOWED_RESEARCH_SUBCOMMANDS = frozenset(
    {
        "backtesting",
        "download-data",
        "list-data",
        "list-exchanges",
        "list-timeframes",
    }
)

FORBIDDEN_FREQTRADE_SUBCOMMANDS = frozenset(
    {
        "trade",
        "webserver",
    }
)

NO_BASELINE_CLAIM = (
    "FreqAI is pinned infrastructure. This adapter does not claim that FreqAI "
    "beats project baselines out of sample."
)

# Local research command (not a Freqtrade CLI subcommand). Never maps to `trade`.
QUANTILE_RESEARCH_COMMAND = "avax-freqai-quantiles"
QUANTILE_MODEL_ID = "freqai.quantiles.research.v1"
QUANTILE_FEATURE_SCHEMA_VERSION = "freqai.quantiles.features.v1"
