"""Canonical hashing for Recursive Learning Harness objects."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False, default=_default)


def sha256_hex(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_digest(payload: Any) -> str:
    return f"sha256:{sha256_hex(payload)}"


def content_hash(payload: dict, hash_field: str = "content_hash") -> str:
    body = {
        key: value
        for key, value in payload.items()
        if key != hash_field and not str(key).startswith("_")
    }
    return sha256_digest(body)


def _default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
