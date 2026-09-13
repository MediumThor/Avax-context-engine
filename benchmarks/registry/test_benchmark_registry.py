#!/usr/bin/env python3
"""Collectable tests for the benchmark registry (not under tests/)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REGISTRY_DIR = Path(__file__).resolve().parent
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from validate import (  # noqa: E402
    ENTRIES_DIR,
    REGISTRY_ROOT,
    REPO_ROOT,
    SCHEMA_PATH,
    RegistryError,
    assert_no_recorded_scores,
    load_json,
    validate_entry,
    validate_registry,
)

REQUIRED_DRAFTS = (
    "avax-5m-next10.draft.json",
    "avax-2026-09-failed-8.draft.json",
)


@pytest.fixture(scope="module")
def schema() -> dict:
    payload = load_json(SCHEMA_PATH)
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def entries() -> dict[str, dict]:
    loaded: dict[str, dict] = {}
    for name in REQUIRED_DRAFTS:
        payload = load_json(ENTRIES_DIR / name)
        assert isinstance(payload, dict)
        loaded[name] = payload
    return loaded


def test_schema_declares_required_fields(schema: dict) -> None:
    required = set(schema["required"])
    assert required == {
        "id",
        "title",
        "dataset_id",
        "time_range",
        "timeframe",
        "metrics",
        "baseline_ids",
        "leakage_rules",
        "status",
        "owner_agent",
    }
    assert set(schema["properties"]["status"]["enum"]) == {"draft", "accepted", "frozen"}


def test_required_draft_files_exist() -> None:
    for name in REQUIRED_DRAFTS:
        assert (ENTRIES_DIR / name).is_file()


def test_registry_validates_clean() -> None:
    assert validate_registry() == []


def test_draft_entries_have_no_scores(entries: dict[str, dict], schema: dict) -> None:
    for name, entry in entries.items():
        validate_entry(entry, schema, ENTRIES_DIR / name)
        assert entry["status"] == "draft"
        assert entry["time_range"]["sealed"] is False
        assert entry["owner_agent"] == "35"
        for metric in entry["metrics"]:
            assert set(metric) <= {"id", "name", "description", "aggregation"}


def test_forecast_entry_is_walk_forward_only(entries: dict[str, dict]) -> None:
    entry = entries["avax-5m-next10.draft.json"]
    assert entry["kind"] == "forecast"
    assert entry["timeframe"] == "5m"
    assert entry["horizons"]["spec"] == "h=1..10"
    assert entry["validation_policy"]["method"] == "chronological_walk_forward"
    assert entry["validation_policy"]["random_shuffle_allowed"] is False
    assert entry["time_range"]["start"] is None
    assert entry["time_range"]["end"] is None
    metric_ids = {item["id"] for item in entry["metrics"]}
    assert metric_ids == {
        "mae",
        "rmse",
        "direction",
        "brier",
        "pinball",
        "interval_coverage",
        "calibration_ece",
    }
    for baseline_id in (
        "zero-return",
        "persistence-drift",
        "ema-trend-heuristic",
        "simple-logistic-direction",
        "simple-linear-return",
    ):
        assert baseline_id in entry["baseline_ids"]


def test_failed_eight_is_pointer_only(entries: dict[str, dict]) -> None:
    entry = entries["avax-2026-09-failed-8.draft.json"]
    assert entry["kind"] == "process_regression"
    assert entry["dataset_ref"] == "benchmarks/rlh/avax-2026-09-failed-8/"
    fixture = REPO_ROOT / "benchmarks/rlh/avax-2026-09-failed-8"
    assert fixture.is_dir()
    manifest = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["as_of_range"][0] == entry["time_range"]["start"]
    assert manifest["as_of_range"][1] == entry["time_range"]["end"]
    assert "outcomes" not in entry
    assert "scores" not in entry


def test_rejects_invented_numeric_score(entries: dict[str, dict], schema: dict) -> None:
    with pytest.raises(RegistryError, match="unexpected property"):
        validate_entry({**entries["avax-5m-next10.draft.json"], "mae": 0.12}, schema)
    with pytest.raises(RegistryError, match="numeric field"):
        assert_no_recorded_scores({"id": "avax-5m-next10", "mae": 0.12})


def test_rejects_missing_required_field(entries: dict[str, dict], schema: dict) -> None:
    broken = copy.deepcopy(entries["avax-5m-next10.draft.json"])
    del broken["baseline_ids"]
    with pytest.raises(RegistryError, match="missing required baseline_ids"):
        validate_entry(broken, schema)


def test_rejects_random_shuffle(entries: dict[str, dict], schema: dict) -> None:
    broken = copy.deepcopy(entries["avax-5m-next10.draft.json"])
    broken["validation_policy"]["random_shuffle_allowed"] = True
    with pytest.raises(RegistryError):
        validate_entry(broken, schema)


def test_rejects_filename_status_mismatch(entries: dict[str, dict], schema: dict) -> None:
    entry = copy.deepcopy(entries["avax-5m-next10.draft.json"])
    with pytest.raises(RegistryError, match="filename status"):
        validate_entry(entry, schema, REGISTRY_ROOT / "entries" / "avax-5m-next10.accepted.json")


def test_readme_and_task_exist() -> None:
    assert (REGISTRY_ROOT / "README.md").is_file()
    assert (REPO_ROOT / "wiki/tasks/WAVE2-35-registry.md").is_file()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
