"""Frozen EncoderMemory builder.

The harness may read this object. It may not write Context Engine state.
A 5m overlay cannot mutate parent timeframe slices.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Iterable, Mapping
from packages.context_engine.models import MarketSnapshot, TimeframeState

from services.harness.hashing import content_hash, sha256_hex

TIMEFRAME_SLICES = ("1w", "1d", "4h", "1h", "15m", "5m")
PARENT_TIMEFRAMES = ("1w", "1d", "4h", "1h", "15m")
HEALTH_VALUES = {"valid", "degraded", "stale", "unknown"}
REGIMES = {
    "bullish",
    "bearish",
    "neutral",
    "transition_up",
    "transition_down",
    "unknown",
}


def _iso(value: datetime | str) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        return value.isoformat().replace("+00:00", "Z")
    return str(value).replace("+00:00", "Z")


def _slice_from_state(state: TimeframeState | Mapping[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {"regime": "unknown", "last_transition_id": None}
    if isinstance(state, TimeframeState):
        return {
            "regime": state.regime if state.regime in REGIMES else "unknown",
            "last_transition_id": None,
            "swing_state": state.swing_state,
            "volatility": state.volatility,
            "as_of": _iso(state.as_of),
        }
    regime = str(state.get("regime", "unknown"))
    if regime not in REGIMES:
        regime = "unknown"
    out = {"regime": regime, "last_transition_id": state.get("last_transition_id")}
    for extra in ("swing_state", "volatility", "as_of"):
        if extra in state:
            out[extra] = state[extra]
    return out


def _snapshot_timeframes(snapshot: MarketSnapshot | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(snapshot, MarketSnapshot):
        return snapshot.timeframes
    return snapshot.get("timeframes", {})


def _snapshot_id(snapshot: MarketSnapshot | Mapping[str, Any], as_of: str) -> str:
    if isinstance(snapshot, MarketSnapshot):
        return f"snapshot-{snapshot.symbol}-{as_of}"
    return str(snapshot.get("id") or snapshot.get("snapshot_id") or f"snapshot-{as_of}")


def _snapshot_symbol(snapshot: MarketSnapshot | Mapping[str, Any]) -> str:
    if isinstance(snapshot, MarketSnapshot):
        return snapshot.symbol
    return str(snapshot.get("symbol", "AVAXUSDT"))


def snapshot_zone_ids(snapshot: MarketSnapshot | Mapping[str, Any]) -> list[str]:
    tfs = _snapshot_timeframes(snapshot)
    ids: list[str] = []
    for state in tfs.values():
        zones = []
        if isinstance(state, TimeframeState):
            zones = list(state.support_zones) + list(state.resistance_zones)
        elif isinstance(state, Mapping):
            zones = list(state.get("support_zones") or []) + list(state.get("resistance_zones") or [])
        for zone in zones:
            zone_id = zone.id if hasattr(zone, "id") else zone.get("id")
            if zone_id and zone_id not in ids:
                ids.append(str(zone_id))
    return ids


def snapshot_hypothesis_ids(snapshot: MarketSnapshot | Mapping[str, Any]) -> list[str]:
    theses = snapshot.theses if isinstance(snapshot, MarketSnapshot) else snapshot.get("theses") or ()
    return [str(row["id"]) for row in theses if isinstance(row, Mapping) and row.get("id")]


def snapshot_analogs(snapshot: MarketSnapshot | Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = snapshot.analogs if isinstance(snapshot, MarketSnapshot) else snapshot.get("analogs") or ()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        if "known_at" in item:
            item["known_at"] = _iso(item["known_at"])
        out.append(item)
    return out


def snapshot_theses(snapshot: MarketSnapshot | Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = snapshot.theses if isinstance(snapshot, MarketSnapshot) else snapshot.get("theses") or ()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        item["known_at"] = _iso(item.get("known_at") or item.get("created_at") or "")
        out.append(item)
    return out


def _closed_only(observations: Iterable[Mapping[str, Any]], as_of: str) -> list[Mapping[str, Any]]:
    kept: list[Mapping[str, Any]] = []
    for item in observations:
        known_at = _iso(item.get("known_at") or item.get("open_time") or as_of)
        if known_at.replace("+00:00", "Z") > as_of.replace("+00:00", "Z"):
            continue
        if item.get("is_closed") is False:
            continue
        if item.get("partial") is True:
            continue
        kept.append(item)
    return kept


def build_encoder_memory(
    *,
    as_of: datetime | str,
    snapshot: MarketSnapshot | Mapping[str, Any],
    forecast_package: Mapping[str, Any],
    data_manifest_id: str,
    feature_schema_version: str = "1",
    context_engine_version: str = "1",
    zone_ids: Iterable[str] | None = None,
    hypothesis_ids: Iterable[str] | None = None,
    cross_market: Mapping[str, Any] | None = None,
    health: str = "valid",
    memory_id: str | None = None,
    observations: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if health not in HEALTH_VALUES:
        raise ValueError(f"invalid encoder health: {health}")
    as_of_iso = _iso(as_of)
    tfs = _snapshot_timeframes(snapshot)
    slices = {name: _slice_from_state(tfs.get(name)) for name in TIMEFRAME_SLICES}
    payload = {
        "id": memory_id or f"encmem-{sha256_hex({'symbol': _snapshot_symbol(snapshot), 'as_of': as_of_iso, 'snapshot': _snapshot_id(snapshot, as_of_iso)})[:16]}",
        "schema_version": "1",
        "symbol": _snapshot_symbol(snapshot),
        "as_of": as_of_iso,
        "context_snapshot_id": _snapshot_id(snapshot, as_of_iso),
        "forecast_package_id": str(forecast_package.get("id", "forecast-unknown")),
        "data_manifest_id": data_manifest_id,
        "feature_schema_version": feature_schema_version,
        "context_engine_version": context_engine_version,
        "timeframe_slices": slices,
        "zone_ids": list(zone_ids or snapshot_zone_ids(snapshot) or forecast_package.get("zone_ids") or []),
        "hypothesis_ids": list(hypothesis_ids if hypothesis_ids is not None else snapshot_hypothesis_ids(snapshot)),
        "cross_market": dict(cross_market or {}),
        "health": health,
    }
    payload["content_hash"] = content_hash(payload)
    if observations is not None:
        # Diagnostic only — not part of the EncoderMemory schema / hash.
        payload["_legal_observation_count"] = len(_closed_only(observations, as_of_iso))
    return payload


def overlay_5m_observation(memory: Mapping[str, Any], five_minute_slice: Mapping[str, Any]) -> dict[str, Any]:
    """Update only the 5m slice. Parent slices are copied unchanged."""
    updated = deepcopy(dict(memory))
    slices = deepcopy(updated["timeframe_slices"])
    parent_before = {name: deepcopy(slices[name]) for name in PARENT_TIMEFRAMES}
    slices["5m"] = _slice_from_state(five_minute_slice)
    updated["timeframe_slices"] = slices
    for name in PARENT_TIMEFRAMES:
        if updated["timeframe_slices"][name] != parent_before[name]:
            raise RuntimeError(f"5m overlay mutated parent slice {name}")
    updated.pop("content_hash", None)
    updated["content_hash"] = content_hash(updated)
    return updated
