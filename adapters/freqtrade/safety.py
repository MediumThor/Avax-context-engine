"""Validate Freqtrade config and strategy source as research/read-only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from adapters.freqtrade.constants import (
    CONFIG_PATH,
    FORBIDDEN_ADAPTER_METHODS,
    FORBIDDEN_FREQTRADE_SUBCOMMANDS,
    PINNED_COMMIT,
    PIN_PATH,
    STRATEGY_PATH,
    UPSTREAM_LICENSE,
    UPSTREAM_REPO,
)


class ResearchOnlyViolation(RuntimeError):
    """Raised when a live-trading, order, or stake-bearing path is requested."""


def load_pin(path: Path | None = None) -> dict[str, Any]:
    payload = json.loads((path or PIN_PATH).read_text(encoding="utf-8"))
    commit = payload.get("commit")
    if commit != PINNED_COMMIT:
        raise ResearchOnlyViolation(
            f"adapter pin {commit!r} does not match required {PINNED_COMMIT}"
        )
    if payload.get("fork") is True:
        raise ResearchOnlyViolation("adapter pin must not declare a fork")
    if payload.get("license") != UPSTREAM_LICENSE:
        raise ResearchOnlyViolation("adapter pin must record GPL-3.0")
    if payload.get("repo") != UPSTREAM_REPO:
        raise ResearchOnlyViolation("adapter pin repo mismatch")
    return payload


def load_research_config(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def validate_research_config(config: dict[str, Any]) -> dict[str, Any]:
    """Assert the FreqAI config cannot live-trade or allocate stake."""
    if config.get("dry_run") is not True:
        raise ResearchOnlyViolation("live trading is forbidden: dry_run must be true")
    if config.get("max_open_trades") != 0:
        raise ResearchOnlyViolation("research config must set max_open_trades to 0")
    stake = config.get("stake_amount")
    if stake in ("unlimited", None) or _as_number(stake) != 0.0:
        raise ResearchOnlyViolation("research config must set stake_amount to 0")
    if "dry_run_wallet" in config and _as_number(config.get("dry_run_wallet")) != 0.0:
        raise ResearchOnlyViolation("research config must set dry_run_wallet to 0")
    if config.get("force_entry_enable") is not False:
        raise ResearchOnlyViolation("force_entry_enable must be false")
    if config.get("initial_state") != "stopped":
        raise ResearchOnlyViolation("initial_state must be stopped")
    trading_mode = config.get("trading_mode", "spot")
    if trading_mode != "spot":
        raise ResearchOnlyViolation("futures/margin trading_mode is forbidden")
    if config.get("margin_mode"):
        raise ResearchOnlyViolation("margin_mode is forbidden in research config")

    exchange = config.get("exchange") or {}
    for secret_key in ("key", "secret", "password", "uid", "walletAddress", "private_key"):
        if exchange.get(secret_key):
            raise ResearchOnlyViolation("exchange credentials are forbidden")
    if "order" in json.dumps(exchange).lower() and any(
        token in json.dumps(exchange).lower()
        for token in ("create_order", "place_order")
    ):
        raise ResearchOnlyViolation("exchange order API configuration is forbidden")

    split = (config.get("freqai") or {}).get("data_split_parameters") or {}
    if split.get("shuffle") is not False:
        raise ResearchOnlyViolation("FreqAI data_split_parameters.shuffle must be false")
    return config


def inspect_strategy_source(path: Path | None = None) -> dict[str, Any]:
    """Parse the strategy file as text so tests do not import Freqtrade/TA-Lib."""
    source = (path or STRATEGY_PATH).read_text(encoding="utf-8")
    lowered = source.lower()
    for method in FORBIDDEN_ADAPTER_METHODS:
        if re.search(rf"\b{re.escape(method)}\s*\(", source):
            raise ResearchOnlyViolation(f"strategy source calls forbidden method {method}()")
    for signal in ("enter_long", "enter_short", "exit_long", "exit_short"):
        if not re.search(rf"""["']{signal}["']\s*\]\s*=\s*0""", source):
            raise ResearchOnlyViolation(f"strategy must keep {signal} at 0")
    if "ccxt" in lowered and "create_order" in lowered:
        raise ResearchOnlyViolation("strategy must not call exchange order APIs")
    return {"path": str(path or STRATEGY_PATH), "research_only": True, "source_chars": len(source)}


def assert_research_subcommand(command: str) -> str:
    name = command.strip().split()[0] if command.strip() else ""
    if not name or name in FORBIDDEN_FREQTRADE_SUBCOMMANDS:
        raise ResearchOnlyViolation(f"freqtrade subcommand {name!r} is forbidden")
    return name


_ORDER_ACTION = re.compile(
    r"(place_.+order|create_.+order|execute_.+order|submit_.+order|cancel_.+order)"
)


def is_forbidden_method(name: str) -> bool:
    normalized = name.lower().strip("_")
    if normalized in FORBIDDEN_ADAPTER_METHODS:
        return True
    return bool(_ORDER_ACTION.search(normalized))
