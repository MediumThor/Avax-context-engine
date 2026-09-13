#!/usr/bin/env python3
"""Validate benchmark registry entries (stdlib only).

Checks JSON Schema subset used by schema.json plus registry-specific
invariants: filename/status match, draft windows unsealed, no recorded
scores, no random-shuffle validation, and RLH fixture pointers exist
without requiring that tree to be edited.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = REGISTRY_ROOT / "schema.json"
ENTRIES_DIR = REGISTRY_ROOT / "entries"
REPO_ROOT = REGISTRY_ROOT.parents[1]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FILENAME_RE = re.compile(r"^([a-z0-9][a-z0-9.-]*)\.(draft|accepted|frozen)\.json$")

FORBIDDEN_RESULT_KEYS = frozenset(
    {
        "accuracy",
        "brier",
        "brier_score",
        "coverage",
        "delta",
        "direction_accuracy",
        "ece",
        "ece_value",
        "improvement",
        "mae",
        "measured",
        "observed",
        "observed_coverage",
        "result",
        "results",
        "rmse",
        "score",
        "scores",
        "threshold",
        "value",
    }
)


class RegistryError(Exception):
    pass


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_ref(schema: dict, ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise RegistryError(f"unsupported $ref {ref}")
    node: object = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise RegistryError(f"unresolved $ref {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise RegistryError(f"$ref {ref} did not resolve to an object")
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
        raise RegistryError(f"unknown type {expected}")
    if expected == "integer" and isinstance(value, bool):
        return False
    return isinstance(value, mapping[expected])


def validate_schema(instance: object, schema: dict, root: dict | None = None, path: str = "$") -> None:
    root = root or schema
    if "$ref" in schema:
        validate_schema(instance, resolve_ref(schema, schema["$ref"], root), root, path)
        return
    if "const" in schema and instance != schema["const"]:
        raise RegistryError(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise RegistryError(f"{path}: {instance!r} not in enum {schema['enum']}")
    if "type" in schema and not type_ok(instance, schema["type"]):
        raise RegistryError(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise RegistryError(f"{path}: shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            raise RegistryError(f"{path}: failed pattern {schema['pattern']}")
        if schema.get("format") == "date-time":
            if not DATE_RE.match(instance):
                raise RegistryError(f"{path}: not UTC date-time Z")
            datetime.strptime(instance, "%Y-%m-%dT%H:%M:%SZ")
    if schema.get("type") == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise RegistryError(f"{path}: below minimum")
    if schema.get("type") == "array" and isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            raise RegistryError(f"{path}: fewer than minItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                validate_schema(item, item_schema, root, f"{path}[{i}]")
    if schema.get("type") == "object" and isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise RegistryError(f"{path}: missing required {key}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                validate_schema(value, properties[key], root, f"{path}.{key}")
            elif additional is False:
                raise RegistryError(f"{path}: unexpected property {key}")
            elif isinstance(additional, dict):
                validate_schema(value, additional, root, f"{path}.{key}")


def _walk(instance: object, path: str = "$"):
    yield path, instance
    if isinstance(instance, dict):
        for key, value in instance.items():
            yield from _walk(value, f"{path}.{key}")
    elif isinstance(instance, list):
        for i, value in enumerate(instance):
            yield from _walk(value, f"{path}[{i}]")


def assert_no_recorded_scores(instance: object) -> None:
    """Schema v1 forbids numeric performance fields anywhere in an entry."""
    for path, value in _walk(instance):
        key = path.rsplit(".", 1)[-1]
        if key in FORBIDDEN_RESULT_KEYS and not path.endswith("].id") and not path.endswith("].name"):
            if not isinstance(value, str):
                raise RegistryError(f"{path}: result-like key must not hold a non-string value")
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            raise RegistryError(f"{path}: numeric field {value!r} looks like a recorded score; schema v1 forbids it")


def assert_utc_range(entry: dict) -> None:
    time_range = entry["time_range"]
    for field in ("start", "end"):
        value = time_range.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not DATE_RE.match(value):
            raise RegistryError(f"time_range.{field} must be UTC Z or null")
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    if entry["status"] == "draft" and time_range.get("sealed") is not False:
        raise RegistryError("draft entries must keep time_range.sealed=false")


def assert_filename(path: Path, entry: dict) -> None:
    match = FILENAME_RE.match(path.name)
    if not match:
        raise RegistryError(f"{path.name}: filename must be {{id}}.{{status}}.json")
    file_id, file_status = match.group(1), match.group(2)
    if file_id != entry.get("id"):
        raise RegistryError(f"{path.name}: filename id {file_id!r} != entry id {entry.get('id')!r}")
    if file_status != entry.get("status"):
        raise RegistryError(f"{path.name}: filename status {file_status!r} != entry status {entry.get('status')!r}")


def assert_validation_policy(entry: dict) -> None:
    policy = entry.get("validation_policy")
    if not policy:
        return
    if policy.get("random_shuffle_allowed") is not False:
        raise RegistryError("random_shuffle_allowed must be false")
    if entry.get("kind") == "forecast" and policy.get("method") != "chronological_walk_forward":
        raise RegistryError("forecast entries must use chronological_walk_forward")


def assert_related_paths(entry: dict) -> None:
    for rel in entry.get("related_paths", []):
        if not isinstance(rel, str):
            raise RegistryError("related_paths items must be strings")
        target = REPO_ROOT / rel
        if not target.exists():
            raise RegistryError(f"related path does not exist: {rel}")
    dataset_ref = entry.get("dataset_ref")
    if isinstance(dataset_ref, str) and dataset_ref.startswith("benchmarks/"):
        target = REPO_ROOT / dataset_ref
        if not target.exists():
            raise RegistryError(f"dataset_ref does not exist: {dataset_ref}")


def validate_entry(entry: object, schema: dict | None = None, path: Path | None = None) -> None:
    if schema is None:
        schema = load_json(SCHEMA_PATH)
        if not isinstance(schema, dict):
            raise RegistryError("schema.json is not an object")
    if not isinstance(entry, dict):
        raise RegistryError("entry must be a JSON object")
    validate_schema(entry, schema)
    assert_no_recorded_scores(entry)
    assert_utc_range(entry)
    assert_validation_policy(entry)
    assert_related_paths(entry)
    if path is not None:
        assert_filename(path, entry)


def iter_entry_paths() -> list[Path]:
    if not ENTRIES_DIR.is_dir():
        raise RegistryError(f"missing entries directory: {ENTRIES_DIR}")
    paths = sorted(ENTRIES_DIR.glob("*.json"))
    if not paths:
        raise RegistryError("no registry entries found")
    return paths


def validate_registry() -> list[str]:
    errors: list[str] = []
    try:
        schema = load_json(SCHEMA_PATH)
        if not isinstance(schema, dict):
            raise RegistryError("schema.json is not an object")
        paths = iter_entry_paths()
    except (OSError, json.JSONDecodeError, RegistryError) as exc:
        return [str(exc)]
    for path in paths:
        try:
            entry = load_json(path)
            validate_entry(entry, schema, path)
        except (OSError, json.JSONDecodeError, RegistryError) as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def main() -> int:
    errors = validate_registry()
    if errors:
        print("FAIL benchmark registry")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("PASS benchmark registry")
    for path in iter_entry_paths():
        print(f"  - {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
