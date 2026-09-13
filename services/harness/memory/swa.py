"""Sliding-window KV for recent loop reasoning. Facts live in EncoderMemory."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Mapping

from services.harness.hashing import sha256_digest

FACT_QUERY_KINDS = {
    "fact",
    "regime",
    "zone",
    "probability",
    "invalidation",
    "forecast",
    "health",
}
REASONING_QUERY_KINDS = {"reasoning", "challenge", "retrieve", "synthesize"}


class SlidingWindow:
    def __init__(self, window_w: int = 16) -> None:
        if window_w < 1:
            raise ValueError("window_w must be >= 1")
        self.window_w = window_w
        self._entries: deque[dict[str, Any]] = deque(maxlen=window_w)
        self.evicted: list[dict[str, Any]] = []

    def __len__(self) -> int:
        return len(self._entries)

    def snapshot(self) -> list[dict[str, Any]]:
        return [deepcopy(item) for item in self._entries]

    def content_hash(self) -> str:
        return sha256_digest({"w": self.window_w, "entries": self.snapshot()})

    def append(self, entry: Mapping[str, Any], *, durable_steps: list[Mapping[str, Any]] | None = None) -> str:
        """Append to the hot window. Evicted items remain in durable_steps if provided."""
        before_hash = self.content_hash()
        payload = dict(entry)
        if len(self._entries) == self.window_w:
            evicted = deepcopy(self._entries[0])
            self.evicted.append(evicted)
            if durable_steps is not None and evicted not in durable_steps:
                durable_steps.append(evicted)
        self._entries.append(payload)
        if durable_steps is not None and payload not in durable_steps:
            durable_steps.append(payload)
        _ = before_hash
        return self.content_hash()


def merge_query(
    query_kind: str,
    *,
    encoder_memory: Mapping[str, Any],
    swa: SlidingWindow,
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """EncoderMemory wins on fact conflicts. SWA supplies recent reasoning only."""
    contradictions: list[str] = []
    if query_kind in FACT_QUERY_KINDS:
        source = "encoder"
        value = {
            "timeframe_slices": encoder_memory.get("timeframe_slices"),
            "zone_ids": encoder_memory.get("zone_ids"),
            "health": encoder_memory.get("health"),
            "forecast_package_id": encoder_memory.get("forecast_package_id"),
        }
    elif query_kind in REASONING_QUERY_KINDS:
        source = "swa"
        value = {"recent": swa.snapshot(), "state": dict(state or {})}
    else:
        source = "both"
        value = {
            "encoder": encoder_memory.get("timeframe_slices"),
            "recent": swa.snapshot(),
            "state": dict(state or {}),
        }
        state_regime = ((state or {}).get("regime_reading") or {}).get("4h")
        encoder_regime = (encoder_memory.get("timeframe_slices") or {}).get("4h", {}).get("regime")
        if state_regime and encoder_regime and state_regime != encoder_regime:
            contradictions.append("encoder_wins_parent_regime")
            value["resolved_4h"] = encoder_regime
    return {
        "source": source,
        "value": value,
        "contradictions": contradictions,
        "encoder_preferred": True,
    }
