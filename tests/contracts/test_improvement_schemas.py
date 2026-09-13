#!/usr/bin/env python3
"""Validate prediction-improvement contracts and examples."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.contracts.test_recursive_schemas import SchemaError, load_json, validate

SCHEMA_DIR = ROOT / "packages" / "contracts" / "improvement"
EXAMPLE_DIR = SCHEMA_DIR / "examples"
WIKI = ROOT / "wiki"

SCHEMA_FILES = {
    "information-gap": "information-gap.schema.json",
    "access-request": "access-request.schema.json",
    "improvement-ticket": "improvement-ticket.schema.json",
    "improvement-outcome": "improvement-outcome.schema.json",
}


def test_schemas_and_examples() -> None:
    for name, filename in SCHEMA_FILES.items():
        schema = load_json(SCHEMA_DIR / filename)
        example = load_json(EXAMPLE_DIR / f"{name}.example.json")
        assert isinstance(schema, dict) and schema.get("title")
        validate(example, schema)


def test_outcome_forbids_execution() -> None:
    schema = load_json(SCHEMA_DIR / "improvement-outcome.schema.json")
    example = load_json(EXAMPLE_DIR / "improvement-outcome.example.json")
    assert example["execution_enabled"] is False
    bad = dict(example)
    bad["execution_enabled"] = True
    try:
        validate(bad, schema)
    except SchemaError:
        return
    raise AssertionError("execution_enabled true must fail validation")


def test_wiki_playbook_linked() -> None:
    home = (WIKI / "Home.md").read_text(encoding="utf-8")
    loop = (WIKI / "Prediction-Improvement-Loop.md").read_text(encoding="utf-8")
    gaps = (WIKI / "Information-Gaps.md").read_text(encoding="utf-8")
    assert "Prediction-Improvement-Loop.md" in home
    assert "Information-Gaps.md" in home
    assert "CONSTITUTION.md" in loop
    assert "does **not** place trades" in loop
    assert "AR-001" in gaps
    assert "GAP-MM-LABELS" in gaps
    assert "I cannot truthfully improve" in loop


def test_access_request_asks_owner() -> None:
    example = load_json(EXAMPLE_DIR / "access-request.example.json")
    assert example["decision"] == "pending"
    assert "GAP-MM-LABELS" in example["owner_prompt"]
    note = (WIKI / "improvement" / "access-requests" / "AR-001-mm-wallet-labels.md").read_text(encoding="utf-8")
    assert "I need from you" in note


if __name__ == "__main__":
    test_schemas_and_examples()
    test_outcome_forbids_execution()
    test_wiki_playbook_linked()
    test_access_request_asks_owner()
    print("all improvement-loop contract tests passed")
