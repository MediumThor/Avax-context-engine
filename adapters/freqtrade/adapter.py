"""Research-only Freqtrade/FreqAI adapter. No live execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.freqtrade.bootstrap import record_upstream_manifest, vendor_dir
from adapters.freqtrade.constants import (
    ALLOWED_RESEARCH_SUBCOMMANDS,
    CONFIG_PATH,
    FORBIDDEN_ADAPTER_METHODS,
    NO_BASELINE_CLAIM,
    PINNED_COMMIT,
    REPO_ROOT,
    UPSTREAM_LICENSE,
    VENDOR_MANIFEST_NAME,
)
from adapters.freqtrade.safety import (
    ResearchOnlyViolation,
    assert_research_subcommand,
    inspect_strategy_source,
    is_forbidden_method,
    load_pin,
    load_research_config,
    validate_research_config,
)


class FreqtradeResearchAdapter:
    """Boundary around pinned upstream Freqtrade. Research and read-only only."""

    def __init__(self, repo_root: Path | None = None, config: dict[str, Any] | None = None) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else REPO_ROOT
        self.pin = load_pin()
        self.config = validate_research_config(config if config is not None else load_research_config())
        inspect_strategy_source()

    def __getattr__(self, name: str) -> Any:
        if is_forbidden_method(name):
            raise ResearchOnlyViolation(
                f"{name} is forbidden: Freqtrade adapter is research/read-only and cannot execute orders"
            )
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")

    def execute(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("execute is forbidden on the research adapter")

    def execute_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("execute_order is forbidden on the research adapter")

    def execute_trade(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("execute_trade is forbidden on the research adapter")

    def place_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("place_order is forbidden on the research adapter")

    def create_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("create_order is forbidden on the research adapter")

    def buy(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("buy is forbidden on the research adapter")

    def sell(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("sell is forbidden on the research adapter")

    def enter_trade(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("enter_trade is forbidden on the research adapter")

    def exit_trade(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("exit_trade is forbidden on the research adapter")

    def force_enter(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("force_enter is forbidden on the research adapter")

    def force_exit(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("force_exit is forbidden on the research adapter")

    def cancel_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("cancel_order is forbidden on the research adapter")

    def live_trade(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("live_trade is forbidden on the research adapter")

    def submit_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("submit_order is forbidden on the research adapter")

    def create_stoploss_order(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("create_stoploss_order is forbidden on the research adapter")

    def cancel_all_orders(self, *args: Any, **kwargs: Any) -> None:
        raise ResearchOnlyViolation("cancel_all_orders is forbidden on the research adapter")

    @property
    def pinned_commit(self) -> str:
        return PINNED_COMMIT

    @property
    def license_id(self) -> str:
        return UPSTREAM_LICENSE

    def research_status(self) -> dict[str, Any]:
        return {
            "mode": "research-read-only",
            "dry_run": True,
            "live_trading": False,
            "stake_amount": 0,
            "max_open_trades": 0,
            "pinned_commit": self.pinned_commit,
            "license": self.license_id,
            "fork": False,
            "freqai_beats_baselines": None,
            "performance_claim": NO_BASELINE_CLAIM,
        }

    def vendor_status(self) -> dict[str, Any]:
        vendor = vendor_dir(self.repo_root)
        manifest_path = vendor / VENDOR_MANIFEST_NAME
        manifest = None
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "vendor_path": str(vendor),
            "cloned": (vendor / ".git").is_dir(),
            "manifest": manifest,
        }

    def record_license(self, vendor: Path | None = None) -> dict[str, Any]:
        return record_upstream_manifest(vendor or vendor_dir(self.repo_root), commit=self.pinned_commit)

    def research_command(self, subcommand: str, *args: str) -> list[str]:
        """Return a research-only argv prefix. Never returns `trade` or order commands."""
        name = assert_research_subcommand(subcommand)
        if name not in ALLOWED_RESEARCH_SUBCOMMANDS:
            raise ResearchOnlyViolation(f"freqtrade subcommand {name!r} is not in the research whitelist")
        return ["freqtrade", name, "--config", str(CONFIG_PATH), *args]


def forbidden_methods() -> frozenset[str]:
    return FORBIDDEN_ADAPTER_METHODS
