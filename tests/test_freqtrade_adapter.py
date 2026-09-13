from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from adapters.freqtrade import (
    FreqtradeResearchAdapter,
    NO_BASELINE_CLAIM,
    PINNED_COMMIT,
    ResearchOnlyViolation,
)
from adapters.freqtrade.bootstrap import record_upstream_manifest
from adapters.freqtrade.constants import (
    ALLOWED_RESEARCH_SUBCOMMANDS,
    FORBIDDEN_ADAPTER_METHODS,
    FORBIDDEN_FREQTRADE_SUBCOMMANDS,
)
from adapters.freqtrade.safety import inspect_strategy_source, load_pin, load_research_config, validate_research_config

REPO = Path(__file__).resolve().parents[1]
PIN = "c064be5325ad6941a2789add795434e6a13dffe9"
BOOTSTRAP = REPO / "scripts" / "bootstrap_freqtrade.sh"
CONFIG = REPO / "adapters" / "freqtrade" / "config.freqai.json"
README = REPO / "adapters" / "freqtrade" / "README.md"
NOTICE = REPO / "adapters" / "freqtrade" / "LICENSE-NOTICE.md"


def test_pin_is_the_required_commit():
    pin = load_pin()
    assert pin["commit"] == PIN == PINNED_COMMIT
    assert pin["license"] == "GPL-3.0"
    assert pin["fork"] is False
    assert pin["complete_clone_required"] is True


def test_config_has_no_live_trading_or_stake():
    config = load_research_config()
    validate_research_config(config)
    assert config["dry_run"] is True
    assert config["stake_amount"] == 0
    assert config["dry_run_wallet"] == 0
    assert config["max_open_trades"] == 0
    assert config["force_entry_enable"] is False
    assert config["initial_state"] == "stopped"
    assert config["trading_mode"] == "spot"
    assert "margin_mode" not in config
    exchange = config["exchange"]
    assert exchange.get("key") in ("", None)
    assert exchange.get("secret") in ("", None)
    assert exchange.get("password") in ("", None)
    assert config["freqai"]["data_split_parameters"]["shuffle"] is False


def test_validate_rejects_live_trading_and_stake():
    config = load_research_config()
    live = dict(config)
    live["dry_run"] = False
    with pytest.raises(ResearchOnlyViolation, match="dry_run"):
        validate_research_config(live)

    staked = dict(config)
    staked["stake_amount"] = 100
    with pytest.raises(ResearchOnlyViolation, match="stake_amount"):
        validate_research_config(staked)

    futures = dict(config)
    futures["trading_mode"] = "futures"
    with pytest.raises(ResearchOnlyViolation, match="trading_mode"):
        validate_research_config(futures)

    keyed = json.loads(json.dumps(config))
    keyed["exchange"]["key"] = "not-a-real-key"
    with pytest.raises(ResearchOnlyViolation, match="credentials"):
        validate_research_config(keyed)

    shuffled = json.loads(json.dumps(config))
    shuffled["freqai"]["data_split_parameters"]["shuffle"] = True
    with pytest.raises(ResearchOnlyViolation, match="shuffle"):
        validate_research_config(shuffled)


def test_adapter_refuses_execute_and_order_methods():
    adapter = FreqtradeResearchAdapter(repo_root=REPO)
    for name in sorted(FORBIDDEN_ADAPTER_METHODS):
        with pytest.raises(ResearchOnlyViolation):
            getattr(adapter, name)()


def test_adapter_refuses_unknown_order_attributes():
    adapter = FreqtradeResearchAdapter(repo_root=REPO)
    with pytest.raises(ResearchOnlyViolation):
        adapter.place_market_order()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        adapter.not_a_real_method()  # type: ignore[attr-defined]


def test_adapter_status_does_not_claim_freqai_beats_baselines():
    status = FreqtradeResearchAdapter(repo_root=REPO).research_status()
    assert status["live_trading"] is False
    assert status["dry_run"] is True
    assert status["stake_amount"] == 0
    assert status["freqai_beats_baselines"] is None
    assert "does not claim" in status["performance_claim"]
    assert status["performance_claim"] == NO_BASELINE_CLAIM
    docs = README.read_text(encoding="utf-8") + NOTICE.read_text(encoding="utf-8")
    assert "beats" not in docs.lower() or "does **not** claim" in docs or "does not claim" in docs


def test_strategy_source_is_research_only_without_importing_freqtrade():
    info = inspect_strategy_source()
    assert info["research_only"] is True
    source = (REPO / "adapters" / "freqtrade" / "AvaxContextStrategy.py").read_text(encoding="utf-8")
    assert 'dataframe["enter_long"] = 0' in source
    assert 'dataframe["enter_short"] = 0' in source
    assert 'dataframe["exit_long"] = 0' in source
    assert 'dataframe["exit_short"] = 0' in source
    assert "create_order" not in source
    assert "place_order" not in source


def test_research_commands_are_whitelisted():
    adapter = FreqtradeResearchAdapter(repo_root=REPO)
    for command in ALLOWED_RESEARCH_SUBCOMMANDS:
        argv = adapter.research_command(command)
        assert argv[0] == "freqtrade"
        assert argv[1] == command
        assert "--config" in argv
    for command in FORBIDDEN_FREQTRADE_SUBCOMMANDS:
        with pytest.raises(ResearchOnlyViolation):
            adapter.research_command(command)
    with pytest.raises(ResearchOnlyViolation):
        adapter.research_command("hyperopt")


def test_bootstrap_script_clones_complete_repo_and_records_license():
    script = BOOTSTRAP.read_text(encoding="utf-8")
    assert PIN in script
    assert "git clone" in script
    assert "--depth" not in script
    assert "sparse-checkout" in script  # rejected, not used
    assert "checkout --detach" in script
    assert "record_upstream_manifest" in script
    assert "LICENSE" in script or "license" in script
    subprocess.run(["bash", "-n", str(BOOTSTRAP)], check=True)
    assert BOOTSTRAP.stat().st_mode & 0o111


def test_record_upstream_manifest_from_mocked_vendor(tmp_path: Path):
    vendor = tmp_path / "freqtrade"
    vendor.mkdir()
    (vendor / "LICENSE").write_text(
        "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n",
        encoding="utf-8",
    )
    payload = record_upstream_manifest(vendor, commit=PIN)
    assert payload["commit"] == PIN
    assert payload["license"] == "GPL-3.0"
    assert payload["license_file"] == "LICENSE"
    assert payload["fork"] is False
    assert payload["copied_into_packages"] is False
    written = json.loads((vendor / ".avax-upstream-manifest.json").read_text(encoding="utf-8"))
    assert written["commit"] == PIN
    assert "GNU GENERAL PUBLIC LICENSE" in written["license_header"]


def test_adapter_loads_without_vendor_freqtrade():
    vendor = REPO / "vendor" / "freqtrade"
    # Tests must not require a cloned upstream tree.
    adapter = FreqtradeResearchAdapter(repo_root=REPO)
    status = adapter.vendor_status()
    assert status["cloned"] is vendor.joinpath(".git").is_dir()
    assert adapter.pinned_commit == PIN
    assert adapter.license_id == "GPL-3.0"
