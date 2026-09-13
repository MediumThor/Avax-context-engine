#!/usr/bin/env python3
"""Validate Recursive Learning Harness JSON schemas and examples.

Stdlib only. Implements the subset of JSON Schema used by
packages/contracts/recursive/*.schema.json.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "packages" / "contracts" / "recursive"
EXAMPLE_DIR = SCHEMA_DIR / "examples"
WIKI = ROOT / "wiki"
CONSTITUTION = ROOT / "CONSTITUTION.md"

SCHEMA_FILES = {
    "encoder-memory": "encoder-memory.schema.json",
    "recurrent-state": "recurrent-state.schema.json",
    "halt-decision": "halt-decision.schema.json",
    "loop-step": "loop-step.schema.json",
    "loop-trace": "loop-trace.schema.json",
    "replay-package": "replay-package.schema.json",
    "loop-outcome": "loop-outcome.schema.json",
}

REQUIRED_FIXTURES = [
    "avax-2026-09-failed-8",
    "no-change-5m",
    "stale-data",
    "invalidation-already-fired",
    "model-disagreement",
    "parent-child-split",
    "analog-cutoff",
    "replay-parity",
]

REQUIRED_WIKI_LINKS = [
    WIKI / "Home.md",
    WIKI / "Architecture.md",
    WIKI / "AI-Harness-Directive.md",
    WIKI / "Watcher-Directive.md",
    WIKI / "Build-Roadmap.md",
]

HALT_REASONS = {
    "max_depth",
    "no_change",
    "challenge_complete",
    "stale_or_unknown_data",
    "contradiction",
    "uncalibrated_confidence",
    "invalidation_move_attempt",
    "latency_budget",
    "watcher_abort",
}

STEP_KINDS = {
    "ENCODE_CHECK",
    "RETRIEVE",
    "SYNTHESIZE",
    "CHALLENGE",
    "FORECAST_REFINE",
    "INVALIDATION_CHECK",
    "ANALOG",
    "NO_CHANGE",
    "HALT",
    "JOURNAL",
}

SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class SchemaError(Exception):
    pass


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_ref(schema: dict, ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise SchemaError(f"unsupported $ref {ref}")
    node: object = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise SchemaError(f"unresolved $ref {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise SchemaError(f"$ref {ref} did not resolve to an object")
    return node


def type_ok(value: object, expected: object) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if isinstance(expected, list):
        return any(type_ok(value, item) for item in expected)
    if expected not in mapping:
        raise SchemaError(f"unknown type {expected}")
    if expected == "integer" and isinstance(value, bool):
        return False
    return isinstance(value, mapping[expected])


def validate(instance: object, schema: dict, root: dict | None = None, path: str = "$") -> None:
    root = root or schema
    if "$ref" in schema:
        validate(instance, resolve_ref(schema, schema["$ref"], root), root, path)
        return
    if "const" in schema and instance != schema["const"]:
        raise SchemaError(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaError(f"{path}: {instance!r} not in enum {schema['enum']}")
    if "type" in schema and not type_ok(instance, schema["type"]):
        raise SchemaError(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")
    if schema.get("type") == "string" or (isinstance(schema.get("type"), list) and "string" in schema["type"] and isinstance(instance, str)):
        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                raise SchemaError(f"{path}: shorter than minLength")
            if "pattern" in schema and not re.search(schema["pattern"], instance):
                raise SchemaError(f"{path}: failed pattern {schema['pattern']}")
            if schema.get("format") == "date-time":
                if not DATE_RE.match(instance):
                    raise SchemaError(f"{path}: not UTC date-time Z")
                datetime.strptime(instance, "%Y-%m-%dT%H:%M:%SZ")
    if schema.get("type") == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaError(f"{path}: below minimum")
    if schema.get("type") == "array" and isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise SchemaError(f"{path}: fewer than minItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                validate(item, item_schema, root, f"{path}[{i}]")
    if schema.get("type") == "object" and isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise SchemaError(f"{path}: missing required {key}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                validate(value, properties[key], root, f"{path}.{key}")
            elif additional is False:
                raise SchemaError(f"{path}: unexpected property {key}")
            elif isinstance(additional, dict):
                validate(value, additional, root, f"{path}.{key}")


def assert_true(cond: bool, message: str) -> None:
    if not cond:
        raise SchemaError(message)


def test_schemas_and_examples() -> list[str]:
    errors: list[str] = []
    for name, filename in SCHEMA_FILES.items():
        schema_path = SCHEMA_DIR / filename
        example_path = EXAMPLE_DIR / f"{name}.example.json"
        try:
            schema = load_json(schema_path)
            example = load_json(example_path)
            assert_true(isinstance(schema, dict), f"{filename} is not an object")
            assert_true(schema.get("title"), f"{filename} missing title")
            validate(example, schema)
        except (OSError, json.JSONDecodeError, SchemaError) as exc:
            errors.append(f"{name}: {exc}")
    return errors


def test_halt_and_kind_alignment() -> list[str]:
    errors: list[str] = []
    halt = load_json(SCHEMA_DIR / "halt-decision.schema.json")
    step = load_json(SCHEMA_DIR / "loop-step.schema.json")
    halt_enum = set(halt["properties"]["reason"]["enum"])
    kind_enum = set(step["properties"]["kind"]["enum"])
    if halt_enum != HALT_REASONS:
        errors.append(f"halt reasons drifted: {halt_enum ^ HALT_REASONS}")
    if kind_enum != STEP_KINDS:
        errors.append(f"step kinds drifted: {kind_enum ^ STEP_KINDS}")
    return errors


def test_parent_child_example() -> list[str]:
    memory = load_json(EXAMPLE_DIR / "encoder-memory.example.json")
    state = load_json(EXAMPLE_DIR / "recurrent-state.example.json")
    errors: list[str] = []
    if memory["timeframe_slices"]["4h"]["regime"] != "bearish":
        errors.append("founding example must keep 4h bearish")
    if memory["timeframe_slices"]["5m"]["regime"] != "bullish":
        errors.append("founding example must show 5m bounce")
    reading = state["regime_reading"]
    if reading.get("4h") != "bearish" or "relief" not in reading.get("interpretation", ""):
        errors.append("recurrent state must not promote 5m bounce to a 4h reversal")
    if state["confidence_source"] not in {"calibrated", "model-disagreement", "insufficient-data"}:
        errors.append("illegal confidence_source")
    return errors


def test_trace_step_order() -> list[str]:
    trace = load_json(EXAMPLE_DIR / "loop-trace.example.json")
    kinds = [step["kind"] for step in trace["steps"]]
    errors: list[str] = []
    if kinds[0] != "ENCODE_CHECK":
        errors.append("LoopTrace example must start with ENCODE_CHECK")
    if kinds[-2:] != ["HALT", "JOURNAL"]:
        errors.append("LoopTrace example must end with HALT then JOURNAL")
    if "CHALLENGE" not in kinds:
        errors.append("directional example must include CHALLENGE")
    if not SHA256_RE.match(trace["content_hash"]):
        errors.append("trace content_hash is not sha256")
    return errors


def test_wiki_discovery() -> list[str]:
    errors: list[str] = []
    needle = "Recursive-Learning-Harness"
    for path in REQUIRED_WIKI_LINKS:
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if needle not in text:
            errors.append(f"{path.name} does not link {needle}")
    return errors


def test_required_fixtures() -> list[str]:
    errors: list[str] = []
    root = ROOT / "benchmarks" / "rlh"
    for fixture_id in REQUIRED_FIXTURES:
        path = root / fixture_id / "expected_invariants.json"
        if not path.exists():
            errors.append(f"missing fixture {fixture_id}")
            continue
        payload = load_json(path)
        if not isinstance(payload, dict) or not payload:
            errors.append(f"{fixture_id} invariants empty")
    return errors


def test_constitution_untouched_marker() -> list[str]:
    text = CONSTITUTION.read_text(encoding="utf-8")
    if "IMMUTABLE PROJECT LAW" not in text:
        return ["CONSTITUTION.md lost its immutable marker"]
    return []


def main() -> int:
    suites = [
        ("schemas+examples", test_schemas_and_examples),
        ("enum alignment", test_halt_and_kind_alignment),
        ("parent/child example", test_parent_child_example),
        ("trace order", test_trace_step_order),
        ("wiki discovery", test_wiki_discovery),
        ("required fixtures", test_required_fixtures),
        ("constitution marker", test_constitution_untouched_marker),
    ]
    failed = 0
    for title, fn in suites:
        errors = fn()
        if errors:
            failed += 1
            print(f"FAIL {title}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {title}")
    if failed:
        print(f"{failed} suite(s) failed")
        return 1
    print("all recursive contract tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
